"""
Custom #flask.Blueprint that needs to be initialized with components.
"""

import flask
from ..base.accesscontrol import AccessControl
from ..base.database import Database
from ..base.storage import Storage


class FaBlueprint(flask.Blueprint):

  accesscontrol = None
  database = None
  storage = None

  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.before_app_first_request(self.__assert_connectors)

  def init_fa_connectors(self, accesscontrol, database, storage):
    """
    Initialize the FatArtifacts connectors for this Flask blueprint.
    """

    self.accesscontrol = accesscontrol
    self.database = database
    self.storage = storage

  def __assert_connectors(self):
    assert isinstance(self.accesscontrol, AccessControl), type(self.accesscontrol)
    assert isinstance(self.database, Database), type(self.database)
    assert isinstance(self.storage, Storage), type(self.storage)
