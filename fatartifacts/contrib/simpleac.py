"""
The "simple" access control implementation has two modes: One that allows any
account full access to groups and artifacts (except that a user without
account can only read) and one that only permits users to access groups
prefixed with their account name.
"""

from ..base import accesscontrol
from typing import *


class SimpleAccessControl(accesscontrol.AccessControl):

  def __init__(self, enforce_prefix=True, isolate=False):
    self.enforce_prefix = enforce_prefix
    self.isolate = isolate

  def get_group_permissions(self, account: Optional[str], group_id: str) -> accesscontrol.Permissions:
    if not account or (self.enforce_prefix and not group_id.startswith(account + '.')):
      if self.isolate:
        return accesscontrol.Permissions.deny_all()
      else:
        return accesscontrol.Permissions.read_only()
    return accesscontrol.Permissions.allow_all()

  def get_artifact_permissions(self, account: Optional[str], group_id: str, artifact_id: str) -> accesscontrol.Permissions:
    return self.get_group_permissions(account, group_id)
