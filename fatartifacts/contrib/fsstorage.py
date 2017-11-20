"""
Local file-system storage implementation.
"""

from ..base import storage
from typing import *
from typing import BinaryIO
import os
import shutil
import tempfile


class FsWriteStream(storage.WriteStream):

  def __init__(self, filename, create_dir=True):
    self._filename = filename
    # XXX ensure temporary file is created on the same device as the output
    #     filename so we can use #os.rename() instead of #shutil.move().
    self._tempfile = tempfile.NamedTemporaryFile(delete=False)
    self._create_dir = create_dir
    self._aborted = False
    self._closed = False

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
    return self._tempfile.write(data)


class FsStorage(storage.Storage):

  def __init__(self, directory: str):
    self.directory = directory

  def get_storage_path(self, group_id: str, artifact_id: str, version: str,
                       tag: str, filename: str) -> str:
    return os.path.join(self.directory, group_id, artifact_id, version,
                        '{}-{}'.format(tag, filename))

  def open_write_file(self, group_id: str, artifact_id: str, version: str,
                      tag: str, filename: str) -> Tuple[storage.WriteStream, str]:
    path = self.get_storage_path(group_id, artifact_id, version, tag, filename)
    return FsWriteStream(path), 'file://' + path

  def open_read_file(self, group_id: str, artifact_id: str, version: str,
                     tag: str, filename: str, uri: str) -> BinaryIO:
    # We must use the URI becaue the filename may contain
    # other characters.
    if not uri.startswith('file://'):
      raise FileNotFoundError(filename)
    #path = self.get_storage_path(group_id, artifact_id, version, tag, filename)
    return open(uri[7:], 'rb')

  def delete_file(self, group_id: str, artifact_id: str, version: str,
                  tag: str, filename: str, uri: str):
    if not uri.startswith('file://'):
      raise FileNotFoundError(filename)
    #path = self.get_storage_path(group_id, artifact_id, version, tag, filename)
    os.remove(uri[7:])
