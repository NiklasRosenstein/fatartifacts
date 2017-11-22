
from fatartifacts.accesscontrol import base


class UserSpaceAccessControl(base.AccessControl):
  """
  The #UserSpaceAccessControl gives full permissions to locations where the
  first level is either the account name or is prefixed with the account name
  plus period. Read access is granted to everyone, unless the *isolate*
  parameter is #True, in which  access to locations outside the userspace
  is denied completely.
  """

  def __init__(self, isolate=False):
    self.isolate = isolate

  def get_permissions(self, location, account):
    if len(location) == 0:
      return base.Permissions.read_only()
    if account and (account == location[0] or location[0].startswith(account + '.')):
      return base.Permissions.allow_all()
    return base.Permissions.read_only()
