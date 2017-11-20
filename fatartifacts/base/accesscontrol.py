"""
Abstraction of access-control.
"""

from typing import *
import abc


class Permissions(NamedTuple):
  can_read: bool
  can_write: bool
  can_delete: bool

  @classmethod
  def allow_all(cls):
    return cls(True, True, True)

  @classmethod
  def deny_all(cls):
    return cls(False, False, False)

  @classmethod
  def read_only(cls):
    return cls(True, False, False)


class AccessControl(metaclass=abc.ABCMeta):

  @abc.abstractmethod
  def get_group_permissions(self, account: Optional[str], group_id: str) -> Permissions:
    pass

  @abc.abstractmethod
  def get_artifact_permissions(self, account: Optional[str], group_id: str, artifact_id: str) -> Permissions:
    pass
