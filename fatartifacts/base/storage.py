"""
Artifact-storage abstraction layer.
"""

from .database import ArtifactObject
from typing import *
from typing import BinaryIO
import abc
import io


class WriteStream(metaclass=abc.ABCMeta):

  def __enter__(self):
    pass

  def __exit__(self, ext_type, exc_value, exc_tb):
    if exc_value is not None:
      self.abort()
    else:
      self.close()

  @abc.abstractmethod
  def abort(self):
    pass

  @abc.abstractmethod
  def close(self):
    pass

  @abc.abstractmethod
  def write(self, data: bytes) -> int:
    pass


# XXX Exception types for errors in the Storage API?

class Storage(metaclass=abc.ABCMeta):

  @abc.abstractmethod
  def open_write_file(self, group_id: str, artifact_id: str, version: str,
                      tag: str, filename: str) -> Tuple[WriteStream, str]:
    """
    Open a file in an artifact object for writing. The #WriteStream interface
    allows you to abort the writing process without destroying the previous
    contents of the file (if it existed).

    This method returns a tuple of the #WriteStream implementation and an URI
    string that uniquely identifies the file. This URI may be a HTTP or HTTPS
    URL.
    """

  @abc.abstractmethod
  def open_read_file(self, group_id: str, artifact_id: str, version: str,
                     tag: str, filename: str, uri: str) -> BinaryIO:
    """
    Open a file for reading. For serving content, you should first check if
    the *uri* is an HTTP or HTTPS URL and serve the content preferably from
    that URL.
    """

  @abc.abstractmethod
  def delete_file(self, group_id: str, artifact_id: str, version: str,
                  tag: str, filename: str, uri: str):
    """
    Delete a file in the storage.
    """
