"""
Abstraction of access-control.
"""

from typing import *
import abc


class Permissions(NamedTuple):
  can_read: bool
  can_write: bool
  can_delete: bool


class AccessControl(metaclass=abc.ABCMeta):

  @abc.abstractmethod
  def get_group_permissions(self, account: Optional[str], group_id: str) -> Permissions:
    pass

  @abc.abstractmethod
  def get_artifact_permissions(self, account: Optional[str], group_id: str, artifact_id: str) -> Permissions:
    pass
