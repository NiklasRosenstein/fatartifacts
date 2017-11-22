"""
Artifact-storage abstraction layer.
"""

from fatartifacts.database.base import Location
from typing import *
from typing import BinaryIO
import abc


class WriteOverflow(Exception):
  """
  This exception is raised if #WriteStream.write() is used to write more data
  than initially allocated in #Storage.open_write_file().
  """


class FileDoesNotExist(Exception):
  """
  Raised when the file being opened with #Storage.open_write_file() does not
  exist. Note that this exception is raised from #Storage.open_read_file()
  or #Storage.delete_file() and the exception itself contains little context
  information.
  """

  def __init__(self, location):
    self.location = location

  def __str__(self):
    return str(self.location)


class UnsupportedLocation(Exception):
  """
  Raised when a database #Location is not supported by the #Storage interface.
  This may implicitly impose restrictions on the characters that may be used
  in locations.
  """

  def __init__(self, location):
    self.location = location

  def __str__(self):
    return str(self.location)


class WriteStream(metaclass=abc.ABCMeta):
  """
  Interface for writable streams opened with #Storage.open_write_file(). If
  you write more data to it than initially allocated with the aforementioned
  method, a #WriteExcessError will be raised from #write().

  WriteStreams can be aborted, preventing the stream's contents to be comitted
  to the #Storage, also keeping previous file contents if the file already
  existed.

  You should consider using the WriteStream as a context-manager. It will
  automatically call #abort() when an exception happened inside the context,
  or #close() otherwise.
  """

  def __enter__(self):
    pass

  def __exit__(self, ext_type, exc_value, exc_tb):
    if exc_value is not None:
      self.abort()
    else:
      self.close()

  @abc.abstractmethod
  def abort(self):
    """
    Abort the stream and prevent the stream's contents from being comitted
    to the #Storage. This method raises a #RuntimeError if #close() was called
    before.
    """

    raise NotImplementedError

  @abc.abstractmethod
  def close(self):
    """
    Close the stream and comitt the contents to the #Storage.
    """

    raise NotImplementedError

  @abc.abstractmethod
  def write(self, data: bytes) -> int:
    """
    Write the binary data in *data* to the stream.
    """

    raise NotImplementedError


class Storage(metaclass=abc.ABCMeta):
  """
  The storage interface allows to place a file for a specific database
  #Location. Files are usually placed at the object-level of the artifact
  repository, thus the storage only needs to support managing files at
  that level (whatever #Database.num_level() returns).
  """

  @abc.abstractmethod
  def supports_location(self, location:Location) -> bool:
    """
    Return #True if the *location* is supported by the storage, ie. that
    #open_write_file() with that location would not raise #UnsupportedLocation.

    Note that this method will implicitly define the valid values for
    locations. The business logic of the artifact repository will use this
    function to check if a location is actually acceptable, EXCEPT for the
    root location. This method may return False for the root location, but
    the root location is always accepted by the business logic.
    """

  @abc.abstractmethod
  def open_write_file(self,
      location:Location, filename:str, content_length:int)\
      -> Tuple[WriteStream, str]:
    """
    Open a file at the specified *location* for writing. The maximum content
    length must be known at the time of opening the file. You may write less
    data than specified in *content_length*.

    Raises:
      UnsupportLocation: If the #Location is not supported by the storage.
    Returns:
       A tuple of the #WriteStream and the file's storage URI that will be
       saved in the database.
    """

    raise NotImplementedError

  @abc.abstractmethod
  def open_read_file(self,
      location:Location, filename:str, uri:str) -> Tuple[BinaryIO, int]:
    """
    Open a file at the specified *location* for reading.

    Raises:
      FileDoesNotExist: If the file does not exist.
    Returns:
      A tuple of the readonly file-like object and the size of the file.
    """

    raise NotImplementedError

  @abc.abstractmethod
  def delete_file(self, location:Location, filename:str, uri:str):
    """
    Deletes the file at the specified *location* and *uri*.

    Raises:
      FileDoesNotExist: If the file does not exist.
    """

    raise NotImplementedError
