"""
Artifact-database abstraction layer.
"""

from typing import *
import abc


class ArtifactObject(NamedTuple):
  tag: str
  filename: str
  uri: str  # This URI must be understood by the configured storage backend.
  mime: str

  def has_web_uri(self):
    return self.uri.startswith('http://') or self.uri.startswith('https://')


class Database(metaclass=abc.ABCMeta):

  @abc.abstractmethod
  def get_group_ids(self) -> Iterable[str]:
    pass

  @abc.abstractmethod
  def get_artifact_ids(self, group_id: str) -> Iterable[str]:
    pass

  @abc.abstractmethod
  def get_artifact_versions(self, group_id: str, artifact_id: str) -> Iterable[str]:
    pass

  @abc.abstractmethod
  def get_artifact_objects(self, group_id: str, artifact_id: str,
                           version: str) -> Iterable[ArtifactObject]:
    pass

  @abc.abstractmethod
  def get_artifact_object(self, group_id: str, artifact_id: str, version: str,
                          tag: str) -> ArtifactObject:
    pass

  @abc.abstractmethod
  def create_artifact(self, group_id: str, artifact_id: str, version: str,
                      object: ArtifactObject):
    pass

  @abc.abstractmethod
  def delete_artifact(self, group_id: str, artifact_id: str, version: str,
                      tag: str) -> ArtifactObject:
    pass


class _ArtifactException(Exception):

  def __init__(self, group_id: str, artifact_id: str, version: str, tag: str):
    self.group_id = group_id
    self.artifact_id = artifact_id
    self.version = version
    self.tag = tag

  def __str__(self):
    return '{}:{}:{}:{}'.format(self.group_id, self.artifact_id, self.version, self.tag)


class ArtifactDoesNotExist(_ArtifactException):
  pass


class ArtifactAlreadyExists(_ArtifactException):
  pass
