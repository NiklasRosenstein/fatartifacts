"""
Storage implementation for Azure Blob Storage.
"""

from ..base import storage
from .fsstorage import BaseFsStorage
from nr.concurrency import Job
from typing import *
from typing import BinaryIO
import collections
import datetime
import functools
import uuid
import requests
import threading
import azure.common


class DualFile(object):
  """
  A file-like object that can be written from one thread and read from
  another. Enables to stream data to a #requests request using dynamically
  generated content.
  """

  def __init__(self, type=bytes):
    assert type in (bytes, str)
    self._type = type
    self._deque = collections.deque()
    self._lock = threading.Lock()
    self._cond = threading.Condition(self._lock)
    self._write_closed = False
    self._read_pos = 0
    self._write_pos = 0

  def read(self, num_bytes=None):
    result = []
    bytes_read = 0
    with self._cond:
      while num_bytes is None or bytes_read < num_bytes:
        if not self._deque and self._write_closed:
          break
        elif not self._deque:
          self._cond.wait()  # wait for more data
        else:
          data = self._deque.popleft()
          if num_bytes and len(data) > num_bytes - bytes_read:
            delta = num_bytes - bytes_read
            data, remainder = data[:delta], data[delta:]
            self._deque.appendleft(remainder)
          result.append(data)
          bytes_read += len(data)
    data = self._type().join(result)
    self._read_pos += len(data)
    return data

  def write(self, data):
    if not isinstance(data, self._type):
      raise TypeError('expected {}, got {}'.format(self._type.__name__, type(data).__name__))
    with self._cond:
      if self._write_closed:
        raise RuntimeError('writing is closed')
      self._deque.append(data)
      self._cond.notify()
    self._write_pos += len(data)
    return len(data)

  def seekable(self):
    return False

  def readable(self):
    return True

  def writable(self):
    return True

  def tell(self):
    return self._read_pos

  def closed(self):
    return False

  def close(self):
    with self._cond:
      self._write_closed = True
      self._cond.notify_all()


class AzureWriteStream(storage.WriteStream):

  def __init__(self, job: Job, fp: BinaryIO, content_length: int):
    self._job = job
    self._fp = fp
    self._content_length = content_length
    self._bytes_written = 0
    self._aborted = False
    self._closed = False

  @property
  def aborted(self):
    return self._aborted

  def abort(self):
    if self._closed and not self._aborted:
      raise RuntimeError('WriteStream already closed, can no longer abort')
    self._aborted = True
    self.close()

  def close(self):
    if not self._closed:
      try:
        self._closed = True
        self._fp.close()
        self._job.wait()
      except:
        self._aborted = True
        raise

  def write(self, data):
    if self._closed:
      raise RuntimeError('WriteStream already closed')
    if self._bytes_written + len(data) > self._content_length:
      raise storage.WriteExcessError()
    self._bytes_written += len(data)
    return self._fp.write(data)


class AzureBlobStorage(BaseFsStorage):

  def __init__(self, blob_service, container: str, **kwargs):
    super().__init__(**kwargs)
    self.blob_service = blob_service
    self.container = container

  def get_blob_name(self, group_id: str, artifact_id: str, version: str,
                    tag: str, filename: str) -> str:
    return '/'.join((
      self.secure_filename(group_id),
      self.secure_filename(artifact_id),
      self.secure_filename(version),
      self.secure_filename(tag + '-' + filename)
    ))

  def find_temporary_blob_name(self):
    # XXX Can we somehow garuantee an unused blob name that will not clash
    #     with another application accessing the blob storage?
    return 'tmp/' + str(uuid.uuid4()) + '.bin'

  def open_write_file(self, group_id: str, artifact_id: str, version: str,
                      tag: str, filename: str, content_length: int) \
                      -> Tuple[storage.WriteStream, str]:
    temp_name = self.find_temporary_blob_name()
    blob_name = self.get_blob_name(group_id, artifact_id, version, tag, filename)
    temp_url = self.blob_service.make_blob_url(self.container, temp_name)
    blob_url = self.blob_service.make_blob_url(self.container, blob_name)
    fp = DualFile()

    def worker():
      self.blob_service.create_blob_from_stream(self.container, temp_name, stream=fp)
      self.blob_service.copy_blob(self.container, blob_name, temp_url)
      self.blob_service.delete_blob(self.container, temp_name)

    job = Job(worker).start()
    return AzureWriteStream(job, fp, content_length), blob_url

  def open_read_file(self, group_id: str, artifact_id: str, version: str,
                     tag: str, filename: str, uri: str) -> Tuple[BinaryIO, int]:
    blob_name = self.get_blob_name(group_id, artifact_id, version, tag, filename)
    try:
      props = self.blob_service.get_blob_properties(self.container, blob_name).properties
    except azure.common.AzureMissingResourceHttpError:
      raise FileNotFoundError(uri)

    fp = DualFile()
    def worker():
      try:
        return self.blob_service.get_blob_to_stream(self.container, blob_name, stream=fp, max_connections=1)
      finally:
        fp.close()

    job = Job(worker).start()
    return fp, props.content_length

  def delete_file(self, group_id: str, artifact_id: str, version: str,
                  tag: str, filename: str, uri: str):
    blob_name = self.get_blob_name(group_id, artifact_id, version, tag, filename)
    try:
      self.blob_service.delete_blob(self.container, blob_name)
    except azure.common.AzureMissingResourceHttpError:
      raise FileNotFoundError(uri)
