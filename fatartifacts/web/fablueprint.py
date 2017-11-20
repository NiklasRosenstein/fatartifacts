"""
Custom #flask.Blueprint that needs to be initialized with components.
"""

import flask
from ..base.accesscontrol import AccessControl
from ..base.database import Database
from ..base.storage import Storage
from .auth import Authorizer
from typing import NamedTuple


class FaConfig(NamedTuple):
  auth: Authorizer = None
  accesscontrol: AccessControl = None
  database: Database = None
  storage: Storage = None
  web_urls_are_public: bool = True


class FaBlueprint(flask.Blueprint):

  fa_config: FaConfig = None

  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.before_app_first_request(self.__assert_connectors)

  def set_fa_config(self, cfg):
    """
    Initialize the FatArtifacts connectors for this Flask blueprint.
    """

    self.fa_config = cfg

  def __assert_connectors(self):
    assert isinstance(self.fa_config.auth, Authorizer), type(self.auth)
    assert isinstance(self.fa_config.accesscontrol, AccessControl), type(self.accesscontrol)
    assert isinstance(self.fa_config.database, Database), type(self.database)
    assert isinstance(self.fa_config.storage, Storage), type(self.storage)

  @property
  def auth(self): return self.fa_config.auth

  @property
  def accesscontrol(self): return self.fa_config.accesscontrol

  @property
  def database(self): return self.fa_config.database

  @property
  def storage(self): return self.fa_config.storage
