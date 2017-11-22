"""
Abstraction of access-control.
"""

from fatartifacts.database.base import Location
from typing import NamedTuple
import abc


class Permissions(NamedTuple):
  can_read: bool
  can_write: bool
  can_delete: bool

  @classmethod
  def allow_all(cls) -> 'Permissions':
    return cls(True, True, True)

  @classmethod
  def deny_all(cls) -> 'Permissions':
    return cls(False, False, False)

  @classmethod
  def read_only(cls) -> 'Permissions':
    return cls(True, False, False)


class AccessControl(metaclass=abc.ABCMeta):
  """
  The access control interface allows fine-grained control over user
  permissions in the database.
  """

  @abc.abstractmethod
  def get_permissions(self, location:Location, account:str=None) -> Permissions:
    """
    Return the permissions for *account* at the specified *location*. If the
    *account* is #None or an empty string, public permissions should be
    returned. Note that it is recommended to keep public permissions at
    #Permissions.read_only().
    """

    raise NotImplementedError
