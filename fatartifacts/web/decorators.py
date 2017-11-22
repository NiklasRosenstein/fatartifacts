
from flask import request
import functools


def check_auth(config):
  def decorator(func):
    """
    Decorator that uses the Web authentication layer creates to create the
    `request.user_id` member.
    """

    @functools.wraps(func)
    def wrapper(*a, **kw):
      try:
        request.user_id = config.auth.do_authorization(request)
      except AuthorizationError as exc:
        abort(403, str(exc))
      return func(*a, **kw)
    return wrapper
  return decorator
