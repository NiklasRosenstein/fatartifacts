"""
Custom #flask.Blueprint that needs to be initialized with components.
"""

import flask
from ..base.accesscontrol import AccessControl
from ..base.database import Database
from ..base.storage import Storage
from .auth import Authorizer


class FaBlueprint(flask.Blueprint):

  auth: Authorizer = None
  accesscontrol: AccessControl = None
  database: Database = None
  storage: Storage = None

  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.before_app_first_request(self.__assert_connectors)

  def init_fa_connectors(self, auth, accesscontrol, database, storage):
    """
    Initialize the FatArtifacts connectors for this Flask blueprint.
    """

    self.auth = auth
    self.accesscontrol = accesscontrol
    self.database = database
    self.storage = storage

  def __assert_connectors(self):
    assert isinstance(self.auth, Authorizer), type(self.auth)
    assert isinstance(self.accesscontrol, AccessControl), type(self.accesscontrol)
    assert isinstance(self.database, Database), type(self.database)
    assert isinstance(self.storage, Storage), type(self.storage)
