"""
Artifact-database abstraction layer.
"""

from fatartifacts.utils.types import NamedObject
from typing import *
import abc
import datetime
import itertools


class Location:
  """
  This class represents a location of an artifact "level". Similar to file
  paths, it consists of several string parts. The maximum number of string
  parts supported is defined by the #Database implementation.

  Object's are stored at the lowest level, at a location that has the maximum
  number of parts supported by the #Database.

  The element separator for a location string is `:`. If the #Location object
  is initialized with a list of parts, a #ValueError is raised if any of the
  parts contains a `:`.

  Passing and empty string or an empty list creates a location that represents
  the root-level of the database.
  """

  __slots__ = ('_parts',)

  def __init__(self, string_or_parts):
    if isinstance(string_or_parts, str):
      parts = string_or_parts.split(':')
      if len(parts) == 1 and not parts[0]:  # empty string
        parts = []
    else:
      parts = list(string_or_parts)
      for part in parts:
        if ':' in part:
          raise ValueError('`:` is an invalid character in a location part string')
    self._parts = parts

  def __str__(self):
    return ':'.join(self._parts)

  def __repr__(self):
    return '<Location {}>'.format(self)

  def __len__(self):
    return len(self._parts)

  def __getitem__(self, index):
    return self._parts[index]

  def __iter__(self):
    yield from self._parts

  def __eq__(self, other):
    if isinstance(other, type(self)):
      return self._parts == other._parts
    return False

  def append(self, *parts):
    """
    Append the specified parts to the location and return a new #Location
    object.
    """

    result = type(self)(itertools.chain(self._parts, parts))
    return result

  @property
  def parent(self):
    """
    Returns the parent of this location. If the location is already the root
    location, #self is returned.
    """

    if not self._parts:
      return self
    return type(self)(self._parts[:-1])

  def validate(self, min_part_length=None, max_part_length=None, valid_chars=None):
    """
    Validates the location parts against the specified criteria. Parts must
    never be empty strings or contain the `:` character, but are otherwise
    free to contain whatever.

    If any of the arguments are supplied, their intended purpose is checked
    against every location part and #False will be returned if the criteria
    is not met.
    """

    for part in self._parts:
      if len(part) == 0 or ':' in part: return False
      if min_part_length is not None and len(part) < min_part_length:
        return False
      if max_part_length is not None and len(part) > max_part_length:
        return False
      if valid_chars is not None and not frozenset(part).issubset(valid_chars):
        return False
    return True


class LocationInfo(NamedObject):
  """
  Contains meta-information about a #Location.
  """

  # The location that this information object is about.
  location: Location

  # Arbitrary metadata for the level.
  metadata: Dict

  # The time the level was created. This field may be #None if the database
  # doesn't support it.
  date_created: datetime.datetime = None

  # The time the level's metadata or any of it's sub-levels where updated.
  # This field may be #None if the database doesn't support it.
  date_updated: datetime.datetime = None


class ObjectInfo(LocationInfo):
  """
  Contains information about an object. An object is stored at the lowest
  level that is supported by the database.
  """

  # The filename of the file represented by the object.
  filename: str

  # The object's mimetype. If the mimetype is unknown, it should
  # be set to `application/octet-stream`.
  mime: str

  # An URI that identifies the object's storage location. This must be
  # compatible with the storage backend. This can also be a web URL in
  # which case it can be passed to API user's directly (the REST-Api has
  # the `web_urls_are_public` option).
  uri: str

  def has_web_uri(self):
    """
    Returns #True if #uri is an http:// or https:// URL.
    """

    return self.uri.startswith('http://') or self.uri.startswith('https://')


class Filter(NamedObject):
  """
  This object can be passed to query functions of the #Database interface to
  filter the result-list. Note that the database is not required to implement
  handling all or any parameters of the #Filter.
  """

  startswith: str = None
  endswith: str = None
  contains: str = None

  # Instructs the database to only return results in #Database.list_location()
  # and #Database.list_objects() that have an object with this "tag" somewhere
  # in the hierarchy.
  has_object: str = None


class _LocationError(Exception):
  def __init__(self, location):
    self.location = location
  def __str__(self):
    return str(self.location)


class LocationAlreadyExists(_LocationError):
  pass


class LocationDoesNotExist(_LocationError):
  pass


class LocationHasChildren(_LocationError):
  pass


class InvalidLocationQuery(_LocationError):
  pass


ObjectDeleteHook = Callable[[ObjectInfo], Any]


class Database(metaclass=abc.ABCMeta):
  """
  The #Database interface is purely for logical storage of the artifact
  repository information. It does not perform physical storage of artifact
  objects and does care about permissions.
  """

  @abc.abstractmethod
  def num_levels(self) -> int:
    """
    Return the number of levels supported by this database. A common scheme
    is to use (group:version:artifact:tag), thus 4 levels. Of course, you can
    also implement the #Database interface where this parameter is configurable.
    Most likely, unless your implementation is very complex and mature, the
    value returned by this method needs to be constant!
    """

    raise NotImplementedError

  @abc.abstractmethod
  def query_context(self) -> ContextManager:
    """
    Return a context manager that needs to be entered before any operations on
    the database are performed. If an exception occurs in inside the context,
    all changes to the database are to be reverted.
    """

    raise NotImplementedError

  @abc.abstractmethod
  def get_location(self, location:Location) -> LocationInfo:
    raise NotImplementedError

  @abc.abstractmethod
  def get_object(self, location:Location) -> ObjectInfo:
    raise NotImplementedError

  @abc.abstractmethod
  def list_location(self, location:Location, filter:Filter=None) -> Iterable[LocationInfo]:
    """
    Queries information about the *location*. If the *filter* parameter is
    specified, not all elements available in that level are returned, but only
    those that match the filter criteria.

    Note that some database implementations may not support all filter options
    and may return more results than matching the filter.

    If the *location* is an object-location or even longer than the supported
    #num_levels(), an #InvalidLocationQuery error will be raised. If the
    *location* pointed to does not exist, a #LocationDoesNotExist error is
    raised.

    Raises:
      LocationDoesNotExist:
      InvalidLocationQuery:
    """

    raise NotImplementedError

  @abc.abstractmethod
  def list_objects(self, location:Location, filter:Filter=None) -> Iterable[ObjectInfo]:
    """
    Queries information about objects at the specified *location*. The
    #Location must have a length equal to or 1 less than #Database.num_levels(),
    otherwise it does not point to a location that contains objects or not
    directly to an object.

    If the location points to an object, the resulting iterable yields one
    #ObjectInfo at maximum (zero if the object does not exist or does not
    match the filter).

    Raises:
      LocationDoesNotExist:
      InvalidLocationQuery:
    """

    raise NotImplementedError

  @abc.abstractmethod
  def create_location(self, info:LocationInfo, update_if_exists=False) -> bool:
    """
    Creates a location from the information in *info*. If the location already
    exists and *update_if_exists* is #False, a #LocationAlreadyExists error is
    raised. Otherwise, the location will be updated.

    If a parent-location does not exist yet, #LocationDoesNotExist will be
    raised.

    The root-location always exists and can only be updated (and not be deleted).

    You can not use this method to create object-locations (ie. locations that
    have length equal to #Database.num_levels()). Use #create_object() instead.

    Raises:
      LocationDoesNotExist:
      LocationAlreadyExists:
      InvalidLocationQuery:
    Returns:
      #True if the location was newly created, #False if it was updated.
    """

    raise NotImplementedError

  @abc.abstractmethod
  def create_object(self, info:ObjectInfo, update_if_exists=False) -> bool:
    """
    Creates an object from the information in *info*. If the object already
    exists and *update_if_exists* is #False, a #LocationAlreadyExists error is
    raised. Otherwise, the object will be updated.

    You can only use this method to create or update object-locations (ie.
    locations that have length equal to #Database.num_levels()).

    Raises:
      LocationDoesNotExist:
      LocationAlreadyExists:
      InvalidLocationQuery:
    Returns:
      #True if the object was newly created, #False if it was updated.
    """

    raise NotImplementedError

  @abc.abstractmethod
  def delete_location(self, location:Location, recursive:bool) -> List[ObjectInfo]:
    """
    Deletes the the location *location*. If it does not exist, a
    #LocationDoesNotExist error is raised. This method can be used to delete
    all locations, including object-levels.

    Note that the root location can not be deleted, but doing so will delete
    all of its sub-locations.

    Raises:
      InvalidLocationQuery:
      LocationDoesNotExist:
      LocationHasChildren: If *recursive* is #False and the location still
        has child locations.
    """

    raise NotImplementedError
