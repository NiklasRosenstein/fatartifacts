"""
Local file-system storage implementation.
"""

from ..base import storage
from typing import *
from typing import BinaryIO
import os
import hashlib
import shutil
import tempfile
import werkzeug.utils


class FsWriteStream(storage.WriteStream):

  def __init__(self, filename: str, content_length: int, create_dir=True):
    self._filename = filename
    # XXX ensure temporary file is created on the same device as the output
    #     filename so we can use #os.rename() instead of #shutil.move().
    self._tempfile = tempfile.NamedTemporaryFile(delete=False)
    self._create_dir = create_dir
    self._aborted = False
    self._closed = False
    self._content_length = content_length
    self._bytes_written = 0

  def abort(self):
    if self._closed and not self._aborted:
      raise RuntimeError('WriteStream already closed, can no longer abort')
    self._closed = True
    self._aborted = True
    self._tempfile.close()
    try:
      os.remove(self._tempfile.name)
    except FileNotFoundError:
      pass

  def close(self):
    if self._closed:
      return
    # XXX atomic file swap?
    self._closed = True
    self._tempfile.close()
    try:
      if self._create_dir:
        os.makedirs(os.path.dirname(self._filename), exist_ok=True)
      try:
        os.remove(self._filename)
      except FileNotFoundError:
        pass
      shutil.move(self._tempfile.name, self._filename)
    finally:
      try:
        os.remove(self._tempfile.name)
      except FileNotFoundError:
        pass

  def write(self, data):
    if self._bytes_written + len(data) > self._content_length:
      raise storage.WriteExcessError()
    written = self._tempfile.write(data)
    self._bytes_written += written
    if written != len(data):
      raise RuntimeError('wrote {} instead of {} bytes'.format(written, len(data)))
    return written


class BaseFsStorage(storage.Storage):

  def __init__(self, prefix_length: int=6):
    self.prefix_length = prefix_length

  def secure_filename(self, name: str) -> str:
    prefix = hashlib.sha1(name.encode('utf8')).hexdigest()[:self.prefix_length]
    return prefix + '-' + werkzeug.utils.secure_filename(name)


class FsStorage(BaseFsStorage):

  def __init__(self, directory: str, prefix_length: int=6):
    super().__init__(prefix_length)
    self.directory = directory

  def get_storage_path(self, group_id: str, artifact_id: str, version: str,
                       tag: str, filename: str) -> str:
    return os.path.join(self.directory,
      self.secure_filename(group_id),
      self.secure_filename(artifact_id),
      self.secure_filename(version),
      self.secure_filename(tag + '-' + filename)
    )

  def open_write_file(self, group_id: str, artifact_id: str, version: str,
                      tag: str, filename: str, content_length: int) \
                      -> Tuple[storage.WriteStream, str]:
    path = self.get_storage_path(group_id, artifact_id, version, tag, filename)
    return FsWriteStream(path, content_length), 'file://' + path

  def open_read_file(self, group_id: str, artifact_id: str, version: str,
                     tag: str, filename: str, uri: str) -> Tuple[BinaryIO, int]:
    # We must use the URI becaue the filename may contain
    # other characters.
    if not uri.startswith('file://'):
      raise FileNotFoundError(filename)
    #path = self.get_storage_path(group_id, artifact_id, version, tag, filename)
    fname = uri[7:]
    size = os.stat(fname).st_size
    return open(fname, 'rb'), size

  def delete_file(self, group_id: str, artifact_id: str, version: str,
                  tag: str, filename: str, uri: str):
    if not uri.startswith('file://'):
      raise FileNotFoundError(filename)
    #path = self.get_storage_path(group_id, artifact_id, version, tag, filename)
    os.remove(uri[7:])
