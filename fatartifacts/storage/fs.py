"""
Local file-system storage implementation.
"""

from fatartifacts.storage import base
import os
import shutil
import string
import tempfile
import werkzeug.utils


class FsWriteStream(base.WriteStream):
  """
  Wrapper for a file on the filesystem. Writes to a temporary file first. Only
  when the WriteStream is closed without exception will the temporary file be
  renamed to the target filename.
  """

  def __init__(self, filename, content_length, create_dir=True):
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
    self._closed = True
    self._tempfile.close()
    try:
      if self._create_dir:
        os.makedirs(os.path.dirname(self._filename), exist_ok=True)
      try:
        os.remove(self._filename)
      except FileNotFoundError:
        pass
      # XXX Ensure atomic file swap?
      shutil.move(self._tempfile.name, self._filename)
    finally:
      try:
        os.remove(self._tempfile.name)
      except FileNotFoundError:
        pass

  def write(self, data):
    if self._bytes_written + len(data) > self._content_length:
      raise base.WriteOverflow()
    written = self._tempfile.write(data)
    self._bytes_written += written
    if written != len(data):
      raise RuntimeError('wrote {} instead of {} bytes'.format(written, len(data)))
    return written


class FsStorage(base.Storage):
  """
  Stores files in a directory on the filesystem.
  """

  supported_chars = frozenset(string.ascii_letters + string.digits + '.-_/@')

  def __init__(self, directory):
    self.directory = directory

  def mkpath(self, location, filename):
    # We want to support / in location parts, so we need a way to avoid
    # name clashes when replacing the / character. We do this by adding the
    # number of / that appeared in the name and replacing the / character
    # by an underscore.
    parts = [str(x.count('/')) + '-' + x.replace('/', '_') for x in location]
    parts[-1] += '-' + werkzeug.utils.secure_filename(filename)
    return os.path.join(self.directory, *parts)

  def getpath(self, location, filename, uri):
    path = self.mkpath(location, filename)
    if uri != 'file://' + path:
      # XXX log to a proper logging facility.
      print('[warning]: URI for location {} has deviated from FS path.'.format(location))
      print('           HAVE   = {}'.format(uri))
      print('           SHOULD = file://{}'.format(path))
      if uri.startswith('file://'):
        path = uri[7:]
      else:
        print('[warning]: URI for location {} is not a file:// URI'.format(location))
        print('           Falling back to generated FS path.')
    return path

  def supports_location(self, location):
    if len(location) == 0: return False
    return location.validate(valid_chars=self.supported_chars)

  def open_write_file(self, location, filename, content_length):
    path = self.mkpath(location, filename)
    return FsWriteStream(path, content_length), 'file://' + path

  def open_read_file(self, location, filename, uri):
    path = self.getpath(location, filename, uri)
    try:
      size = os.stat(path).st_size
      return open(path, 'rb'), size
    except FileNotFoundError:
      raise base.FileDoesNotExist(location)

  def delete_file(self, location, filename, uri):
    path = self.getpath(location, filename, uri)
    try:
      os.remove(path)
    except FileNotFoundError:
      raise base.FileDoesNotExist(location)
