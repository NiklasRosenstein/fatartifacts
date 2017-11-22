"""
Storage implementation for Azure Blob Storage.
"""

from fatartifacts.storage import base
from fatartifacts.utils.io import ThreadedRWIO
from nr.concurrency import Job
import azure.common
import azure.storage.blob
import string
import uuid
import threading
import werkzeug.utils


class AzureWriteStream(base.WriteStream):
  """
  A #stsorage.WriteStream implementation that writes to a #ThreadedRWIO
  which is passed to the Azure request.

  Arguments:
    job: The #Job that performs the Azure request.
    fp: A #ThreadedRWIO instance that the object will write to.
    content_length: The maximum content length.
  """

  def __init__(self, job, fp, content_length):
    self._job = job
    self._fp = fp
    self._content_length = content_length
    self._bytes_written = 0
    self._aborted = False
    self._closed = False
    self._closed_event = threading.Event()

  @property
  def aborted(self):
    return self._aborted

  def wait_until_closed(self):
    self._closed_event.wait()

  def abort(self):
    if self._closed and not self._aborted:
      raise RuntimeError('WriteStream already closed, can no longer abort')
    self._aborted = True
    self.close()

  def close(self):
    try:
      if not self._closed:
        self._closed = True
        self._fp.close()
        self._closed_event.set()
        self._job.wait()
    except:
      self._aborted = True
      raise

  def write(self, data):
    if self._closed:
      raise RuntimeError('WriteStream already closed')
    if self._bytes_written + len(data) > self._content_length:
      raise base.WriteOverflow()
    self._bytes_written += len(data)
    return self._fp.write(data)


class AzureBlobStorage(base.Storage):
  """
  An implementation of the #base.Storage interface that communicates with
  an Azure Blob Storage service.

  Args:
    blob_s
  """

  supported_chars = frozenset(string.ascii_letters + string.digits + '.-_/@')

  @classmethod
  def with_block_blob_service(cls, container, *args, **kwargs):
    service = azure.storage.blob.BlockBlobService(*args, **kwargs)
    return cls(container, service)

  @classmethod
  def with_page_blob_service(cls, container, *args, **kwargs):
    service = azure.storage.blob.PageBlobService(*args, **kwargs)
    return cls(container, service)

  @classmethod
  def with_append_blob_service(cls, container, *args, **kwargs):
    service = azure.storage.blob.AppendBlobService(*args, **kwargs)
    return cls(container, service)

  def __init__(self, container, service):
    self.service = service
    self.container = container

  def blob_name(self, location, filename):
    # Since / is the directory separator on Azure but we support / in the
    # location parts, and : is the location separator, we simply swap : and /.
    # Unlike the FsStorage, : is supported in Azure blob names.
    name = str(location).replace('/', ':')
    return 'data/' + name + '/' + werkzeug.utils.secure_filename(filename)

  def temporary_blob_name(self):
    """
    Returns a temporary blob name using a UUID.

    XXX Can we somehow garuantee that the blob name stays unused for the
        whole operation that we use it for? Maybe using the blob service's
        locking mechanism would help.
    """

    return 'tmp/' + str(uuid.uuid4()) + '.bin'

  def supports_location(self, location):
    if len(location) == 0: return False
    return location.validate(valid_chars=self.supported_chars)

  def open_write_file(self, location, filename, content_length):
    if not self.supports_location(location):
      raise base.UnsupportedLocation(location)

    # We write to a temporary blob and only copy to the actual blob
    # when the AzureWriteStream is closed successfully.
    temp_name = self.temporary_blob_name()
    blob_name = self.blob_name(location, filename)
    temp_url = self.service.make_blob_url(self.container, temp_name)
    blob_url = self.service.make_blob_url(self.container, blob_name)
    fp = ThreadedRWIO()
    awstream = None

    def worker():
      self.service.create_blob_from_stream(self.container, temp_name, stream=fp)
      awstream.wait_until_closed()
      if not awstream.aborted:
        self.service.copy_blob(self.container, blob_name, temp_url)
      self.service.delete_blob(self.container, temp_name)

    job = Job(worker).start()
    awstream = AzureWriteStream(job, fp, content_length)
    return awstream, blob_url

  def open_read_file(self, location, filename, uri):
    blob_name = self.blob_name(location, filename)
    try:
      props = self.service.get_blob_properties(
          self.container, blob_name).properties
    except azure.common.AzureMissingResourceHttpError:
      raise base.FileDoesNotExist(location)
    except azure.common.AzureMissingResourceHttpError as e:
      raise base.PermissionError(e)
    fp = ThreadedRWIO()
    def worker():
      try:
        return self.service.get_blob_to_stream(
            self.container, blob_name, stream=fp, max_connections=1)
      finally:
        fp.close()
    job = Job(worker).start()
    return fp, props.content_length

  def delete_file(self, location, filename, uri):
    blob_name = self.blob_name(location, filename)
    try:
      self.service.delete_blob(self.container, blob_name)
    except azure.common.AzureMissingResourceHttpError:
      raise base.FileDoesNotExist(location)
