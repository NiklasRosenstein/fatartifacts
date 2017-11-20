"""
Authentication layer for the FatArtifacts web server.
"""

from typing import *
import abc
import flask
import hashlib


class Authorizer(metaclass=abc.ABCMeta):

  @abc.abstractmethod
  def do_authorization(self, request: flask.Request) -> Optional[str]:
    pass


class AuthorizationError(Exception):
  pass



class HardcodedAuthorizer(Authorizer):

  def __init__(self, users, encoding='utf8'):
    self.users = {}
    self.encoding = encoding
    for user, pw in users.items():
      method, value = pw.partition(':')[::2]
      if method not in hashlib.algorithms_available:
        raise ValueError('unknown hash algorithm: {}'.format(method))
      self.users[user] = (method, value)

  def do_authorization(self, request: flask.Request) -> Optional[str]:
    auth = request.authorization
    if not auth:
      return None  # global access, no account
    if auth.username not in self.users:
      raise AuthorizationError('Invalid username.')
    method, value = self.users[auth.username]
    hashed_pw = hashlib.new(method, auth.password.encode(self.encoding)).hexdigest()
    if hashed_pw != value:
      raise AuthorizationError('Invalid password')
    return auth.username
