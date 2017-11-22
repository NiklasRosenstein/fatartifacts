"""
Pony-ORM database backend.
"""

from fatartifacts.database import base
from datetime import datetime
from pony import orm
from typing import *
import threading


def declare_entities(db):

  class Location(db.Entity):
    name = orm.Optional(str)
    parent = orm.Optional('Location', reverse='children')
    children = orm.Set('Location', cascade_delete=True)
    metadata = orm.Required(orm.Json)
    date_created = orm.Required(datetime)
    date_updated = orm.Required(datetime)
    object = orm.Optional('Object', cascade_delete=True)
    orm.composite_index(name, parent)

    @staticmethod
    def get_root() -> 'Location':
      root = Location.get(name='', parent=None)
      if not root:
        now = datetime.utcnow()
        root = Location(name='', parent=None, metadata={}, date_created=now,
                   date_updated=now)
      return root

    @classmethod
    def get_by_db_location(cls, loc:base.Location) -> Optional['Location']:
      current = cls.get_root()
      for i in range(len(loc)):
        current = cls.get(name=loc[i], parent=current)
        if not current:
          return None
      return current

    @classmethod
    def from_db_location(cls, loc:base.Location, metadata:Dict) -> 'Location':
      now = datetime.utcnow()
      parent = cls.get_by_db_location(loc.parent)
      if not parent:
        raise base.LocationDoesNotExist(loc.parent)
      entity = cls(name=loc[-1], parent=parent, metadata=metadata,
                   date_created=now, date_updated=now)
      return entity

    def as_db_location(self) -> base.Location:
      parts = []
      while self:
        if not self.name:
          assert self == Location.get_root()
          break
        parts.append(self.name)
        self = self.parent
      return base.Location(reversed(parts))

    def as_db_location_info(self) -> base.LocationInfo:
      return base.LocationInfo(
        self.as_db_location(),
        self.metadata,
        self.date_created,
        self.date_updated)

    def collect_objects(self) -> Iterable['Object']:
      if self.object: yield self.object
      for child in self.children:
        yield from child.collect_objects()

    def validate(self):
      if not self.name and self.parent:
        raise ValueError('non-root level can not have a zero-length name')

    def before_insert(self):
      self.validate()

    def before_update(self):
      self.date_updated = datetime.utcnow()
      self.validate()

  class Object(db.Entity):
    location = orm.PrimaryKey(Location)
    filename = orm.Required(str)
    mime = orm.Required(str)
    uri = orm.Required(str)

    @classmethod
    def from_db_location(cls, loc:base.Location, metadata:Dict,
                         filename: str, mime: str, uri: str) -> 'Object':
      location = Location.from_db_location(loc, metadata)
      now = datetime.utcnow()
      entity = cls(location=location, filename=filename, mime=mime, uri=uri)
      return entity

    def as_db_object_info(self) -> base.ObjectInfo:
      return base.ObjectInfo(
        self.location.as_db_location(),
        self.location.metadata,
        self.location.date_created,
        self.location.date_updated,
        self.filename,
        self.mime,
        self.uri)


class PonyDatabase(base.Database):

  def __init__(self, num_levels):
    self._num_levels = num_levels
    self._db = orm.Database()
    declare_entities(self._db)

  def connect(self, *args, **kwargs):
    create_tables = kwargs.pop('create_tables', True)
    self._db.bind(*args, **kwargs)
    self._db.generate_mapping(create_tables=create_tables)

    with orm.db_session():
      self._db.Location.get_root()  # ensure that the root exists.

  def num_levels(self):
    return self._num_levels

  def query_context(self):
    return orm.db_session

  def get_location(self, location):
    if len(location) >= self._num_levels:
      raise base.InvalidLocationQuery(location)
    entity = self._db.Location.get_by_db_location(location)
    if not entity:
      raise base.LocationDoesNotExist(location)
    return entity.as_db_location_info()

  def get_object(self, location):
    if len(location) != self._num_levels:
      raise base.InvalidLocationQuery(location)
    entity = self._db.Location.get_by_db_location(location)
    if not entity:
      raise base.LocationDoesNotExist(location)
    return entity.object.as_db_object_info()

  def list_location(self, location, filter=None):
    # XXX Implement filter.
    if len(location) >= self._num_levels:
      raise base.InvalidLocationQuery(location)
    entity = self._db.Location.get_by_db_location(location)
    if not entity:
      raise base.LocationDoesNotExist(location)
    return (x.as_db_location_info() for x in entity.children)

  def list_objects(self, location, filter=None):
    # XXX Implement filter.
    if len(location) not in (self._num_levels, self._num_levels - 1):
      raise base.InvalidLocationQuery(location)
    entity = self._db.Location.get_by_db_location(location)
    if not entity:
      raise base.LocationDoesNotExist(location)
    if len(location) == self._num_levels:
      yield entity.object.as_db_object_info()
    else:
      yield from (x.object.as_db_object_info() for x in entity.children if x.object)

  def create_location(self, info, update_if_exists=False):
    if len(info.location) > (self._num_levels - 1):
      raise base.InvalidLocationQuery(info.location)
    entity = self._db.Location.get_by_db_location(info.location)
    if entity and not update_if_exists:
      raise base.LocationAlreadyExists(info.location)
    if entity:
      if info.metadata is not None:
        entity.metadata = info.metadata
      return False  # updated
    else:
      entity = self._db.Location.from_db_location(
        info.location,
        metadata=info.metadata or {})
      assert entity.as_db_location() == info.location, (entity.as_db_location(), info.location)
      return True  # newly created location

  def create_object(self, info, update_if_exists=False):
    if len(info.location) != self._num_levels:
      raise base.InvalidLocationQuery(info.location)
    entity = self._db.Location.get_by_db_location(info.location)
    if entity and not update_if_exists:
      raise base.LocationAlreadyExists(info.location)
    if entity:
      if info.metadata is not None:
        entity.metadata = info.metadata
      if entity.object:
        entity.object.filename = info.filename
        entity.object.mime = info.mime
        entity.object.uri = info.uri
      else:
        entity.object = self._db.Object(location=entity,
            filename=info.filename, uri=info.uri, mime=info.mime)
      return False  # updated
    else:
      entity = self._db.Object.from_db_location(
        info.location,
        metadata=info.metadata or {},
        filename=info.filename,
        mime=info.mime,
        uri=info.uri)
      assert entity.location.as_db_location() == info.location, (entity.as_db_location(), info.location)
      return True  # newly created location

  def delete_location(self, location, recursive):
    if len(location) > self._num_levels:
      raise base.InvalidLocationQuery(location)

    entity = self._db.Location.get_by_db_location(location)
    if not entity:
      raise base.LocationDoesNotExist(location)

    if entity.children and not recursive:
      raise base.LocationHasChildren(location)

    objects = [x.as_db_object_info() for x in entity.collect_objects()]
    if len(location) == 0:
      # The root location can not be deleted, but it's children can be.
      entity.children.select().delete()
    else:
      if not entity:
        raise base.LocationDoesNotExist(location)
      entity.delete()

    return objects
