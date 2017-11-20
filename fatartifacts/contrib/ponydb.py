"""
Pony-ORM database backend.
"""

from ..base import database
from pony import orm
from typing import *


def declare_models(db):

  class Group(db.Entity):
    id = orm.PrimaryKey(str)
    artifacts = orm.Set('Artifact')

    @classmethod
    def get_or_create(cls, id: str) -> 'Group':
      group = cls.get(id=id)
      if not group:
        group = cls(id=id)
      return group


  class Artifact(db.Entity):
    group = orm.Required(Group)
    id = orm.Required(str)
    orm.PrimaryKey(id, group)
    versions = orm.Set('Version')

    @classmethod
    def get_or_create(cls, group: Group, id: str, ) -> 'Artifact':
      artifact = cls.get(group=group, id=id)
      if not artifact:
        artifact = cls(group=group, id=id)
      return artifact

  class Version(db.Entity):
    artifact = orm.Required(Artifact)
    string = orm.Required(str)
    orm.PrimaryKey(artifact, string)
    objects = orm.Set('Object')

    @classmethod
    def get_or_create(cls, artifact: Artifact, string: str) -> 'Version':
      version = cls.get(artifact=artifact, string=string)
      if not version:
        version = cls(artifact=artifact, string=string)
      return version

  class Object(db.Entity):
    version = orm.Required(Version)
    tag = orm.Required(str)
    filename = orm.Required(str)
    uri = orm.Required(str)
    mime = orm.Required(str)
    orm.PrimaryKey(version, tag)


class PonyDatabase(database.Database):

  def __init__(self):
    self.db = orm.Database()
    declare_models(self.db)

  def connect(self, *args, **kwargs):
    create_tables = kwargs.pop('create_tables', True)
    self.db.bind(*args, **kwargs)
    self.db.generate_mapping(create_tables=create_tables)

  @orm.db_session
  def get_group_ids(self) -> Iterable[str]:
    return iter(orm.select(g.id for g in self.db.Group))

  @orm.db_session
  def get_artifact_ids(self, group_id: str) -> Iterable[str]:
    group = self.db.Group.get(id=group_id)
    if not group:
      return []
    return iter(orm.select(a.id for a in self.db.Artifact if a in group.artifacts))

  @orm.db_session
  def get_artifact_versions(self, group_id: str, artifact_id: str) -> Iterable[str]:
    group = self.db.Group.get(id=group_id)
    if not group:
      return []
    artifact = self.db.Artifact.get(group=group, id=artifact_id)
    if not artifact:
      return []
    return iter(orm.select(v.string for v in self.db.Version if v in artifact.versions))

  @orm.db_session
  def get_artifact_objects(self, group_id: str, artifact_id: str,
                           version: str) -> Iterable[database.ArtifactObject]:
    group = self.db.Group.get(id=group_id)
    if not group:
      return []
    artifact = self.db.Artifact.get(group=group, id=artifact_id)
    if not artifact:
      return []
    version = self.db.Version.get(artifact=artifact, string=version)
    if not version:
      return []
    return iter(
      database.ArtifactObject(tag=o.tag, filename=o.filename, uri=o.uri, mime=o.mime)
      for o in version.objects
    )

  @orm.db_session
  def get_artifact_object(self, group_id: str, artifact_id: str,
                          version: str, tag: str) -> database.ArtifactObject:
    group = self.db.Group.get(id=group_id)
    if not group:
      raise database.ArtifactDoesNotExist(group_id, artifact_id, version, tag)
    artifact = self.db.Artifact.get(group=group, id=artifact_id)
    if not artifact:
      raise database.ArtifactDoesNotExist(group_id, artifact_id, version, tag)
    version = self.db.Version.get(artifact=artifact, string=version)
    if not version:
      raise database.ArtifactDoesNotExist(group_id, artifact_id, version, tag)
    obj = self.db.Object.get(version=version, tag=tag)
    if not obj:
      raise database.ArtifactDoesNotExist(group_id, artifact_id, version, tag)
    return database.ArtifactObject(tag=obj.tag, filename=obj.filename, uri=obj.uri, mime=obj.mime)

  @orm.db_session
  def create_artifact(self, group_id: str, artifact_id: str, version: str,
                      object: database.ArtifactObject):
    group = self.db.Group.get_or_create(group_id)
    artifact = self.db.Artifact.get_or_create(group, artifact_id)
    version = self.db.Version.get_or_create(artifact, version)
    obj = self.db.Object.get(version=version, tag=object.tag)
    if obj:
      raise database.ArtifactAlreadyExists(group_id, artifact_id, version.string, object.tag)
    self.db.Object(version=version, tag=object.tag, filename=object.filename,
      uri=object.uri, mime=object.mime)

  @orm.db_session
  def delete_artifact(self, group_id: str, artifact_id: str, version: str,
                      tag: str) -> database.ArtifactObject:
    group = self.db.Group.get_or_create(group_id)
    artifact = self.db.Artifact.get_or_create(group, artifact_id)
    version = self.db.Version.get_or_create(artifact, version)
    obj = self.db.Object.get(version=version, tag=tag)
    if not obj:
      raise database.ArtifactDoesNotExist(group_id, artifact_id, version.string, tag)
    result = database.ArtifactObject(obj.tag, obj.filename, obj.uri, obj.mime)
    obj.delete()
    return result
