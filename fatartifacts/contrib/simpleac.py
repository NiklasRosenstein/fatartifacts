"""
The "simple" access control implementation has two modes: One that allows any
account full access to groups and artifacts (except that a user without
account can only read) and one that only permits users to access groups
prefixed with their account name.
"""

from ..base import accesscontrol
from typing import *


class SimpleAccessControl(accesscontrol.AccessControl):

  def __init__(self, limit_to_prefix=True):
    self.limit_to_prefix = limit_to_prefix

  def get_group_permissions(self, account: Optional[str], group_id: str) -> accesscontrol.Permissions:
    if not account or (self.limit_to_prefix and not group_id.startswith(account + '.')):
      return accesscontrol.Permissions(can_read=True, can_write=False, can_delete=False)
    return accesscontrol.Permissions(can_read=True, can_write=True, can_delete=True)

  def get_artifact_permissions(self, account: Optional[str], group_id: str, artifact_id: str) -> accesscontrol.Permissions:
    return self.get_group_permissions(account, group_id)
