
from .auth import AuthorizationError
from .decorators import check_auth
from fatartifacts.database import base as database
from fatartifacts.storage import base as storage
from flask import abort, current_app, redirect, request, url_for, send_file, Blueprint, Response
from werkzeug.exceptions import HTTPException
import datetime
import functools
import json
import shutil
import werkzeug.local

app = Blueprint(__name__, __name__)
app.config = None
config = werkzeug.local.LocalProxy(lambda: app.config)


class Config:
  """
  Examplary configuration for the REST-Api Blueprint.
  """

  auth: 'fatartifacts.auth.base.Authorizer' = None
  accesscontrol: 'fatartifacts.auth.accesscontrol.AccessControl' = None
  database: 'fatartifacts.auth.database.Database' = None
  storage: 'fatartifacts.auth.storage.Storage' = None
  web_urls_are_public: bool = True


def jsonify(cls=None):
  """
  Simple decorator to ensure that a JSON response is sent.
  """

  def decorator(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
      try:
        result = func(*args, **kwargs)
        if isinstance(result, tuple):
          result, status = result
        else:
          status = 200
        return Response(json.dumps(result, cls=cls), status=status, mimetype='text/json')
      except HTTPException as e:
        return Response(json.dumps({
          'message': str(e)
        }), status=e.code, mimetype='text/json')
      except Exception as e:
        current_app.logger.exception(e)
        return Response(json.dumps({
          'message': 'The server has encountered an internal server error.'
        }), status=500, mimetype='text/json')
    return wrapper

  return decorator


class JsonEncoder(json.JSONEncoder):
  """
  Our custom JSON encoder that is capable of encoding datetime.
  """

  def default(self, o):
    if isinstance(o, datetime.datetime):
      return str(o)
    return super().default(o)


def close_input_stream(func):
  """
  A decorator that ensures that the `wsgi.input` stream is closed. This is
  necessary a request aborts before the stream is exhausted, as otherwise
  the **client** will close the connection with an error.
  """

  @functools.wraps(func)
  def wrapper(*a, **kw):
    try:
      return func(*a, **kw)
    finally:
      fp = request.environ.get('wsgi.input')
      if fp:
        fp.close()
  return wrapper


def check_bool_header(header_name, default=False):
  value = request.headers.get(header_name, None)
  if value is None:
    return default
  value = value.strip().lower()
  if value in ('1', 'yes', 'true', 'on', 'enabled'):
    return True
  return False


def get_object_url(info: database.ObjectInfo, default=NotImplemented) -> str:
  """
  Returns the publicly accessible URL for the object. If the object already
  has a web URL as URI and the `web_urls_are_public` configuration option is
  enabled, that URL is returned as is. Otherwise, it will return the URL to
  read the object's data using the #read() route.
  """

  if info.has_web_uri() and config.web_urls_are_public:
    return info.uri
  if default is NotImplemented:
    return url_for(__name__ + '.read', path=str(info.location))
  return default


def get_location_as_json(loc):
  def object_to_json(x):
    return {
      'location': str(x.location),
      'metadata': x.metadata,
      'dateCreated': x.date_created,
      'dateUpdated': x.date_updated,
      'filename': x.filename,
      'url': get_object_url(x),
      'mime': x.mime
    }
  def location_to_json(x):
    return {
      'location': str(x.location),
      'metadata': x.metadata,
      'dateCreated': x.date_created,
      'dateUpdated': x.date_updated
    }

  ac = config.accesscontrol
  assert ac.get_permissions(loc, request.user_id).can_read  # already verified

  is_object = len(loc) == config.database.num_levels()
  if is_object:
    return 'object', object_to_json(config.database.get_object(loc))

  result = location_to_json(config.database.get_location(loc))
  if len(loc) == config.database.num_levels() - 1:  # Children are objects
    result['objects'] = [
      object_to_json(x) for x in config.database.list_objects(loc)
      if ac.get_permissions(x.location, request.user_id).can_read
    ]
  else:
    result['children'] = [
      location_to_json(x) for x in config.database.list_location(loc)
      if ac.get_permissions(x.location, request.user_id).can_read
    ]

  return 'location', result


@close_input_stream
def _handle_put_object(loc):
  """
  Handles the upload of an object's file and metadata. The metadata must be
  streamed before the file contents. The following headers are required:

  * Content-Length: <length of the full payload, metadata + file>
  * Content-Type: application/vnd.fatartifacts+putobject
  * X-Metadata-Length: <the length in bytes of the JSON metadata>
  * X-Metadata-Encoding: <optional, the encoding of the JSON metadata. Defaults to utf8>
  * X-File-Name: <the name of the uploaded file>
  * X-File-ContentType: <the MIME type of the uploaded file>
  * X-Update-If-Exists: If this header is set and not empty, the object
    will be updated if it already exists, otherwise a 409 error is returned.

  The request body has no special delimiters or encoding, but is simply split
  into two blocks:

        [       METADATA (X-Metadata-Length bytes)        ]
        [ FILE (Content-Length - X-Metadata-Length bytes) ]
  """

  content_length = request.headers.get('Content-Length', '')
  try:
    content_length = int(content_length)
    if content_length <= 0:
      raise ValueError
  except ValueError:
    abort(400, 'Missing or invalid Content-Length header.')

  content_type = request.headers.get('Content-Type', '')
  expect_type = 'application/vnd.fatartifacts+putobject'
  if content_type != expect_type:
    abort(400, 'Expected Content-Type: {}, got {}'.format(expect_type, content_type))

  metadata_length = request.headers.get('X-Metadata-Length', '')
  try:
    metadata_length = int(metadata_length)
    if metadata_length <= 0 or metadata_length > content_length:
      raise ValueError
  except ValueError:
    abort(400, 'Missing or invalid X-Metadata-Length header.')

  file_name = request.headers.get('X-File-Name', '')
  file_content_type = request.headers.get('X-File-ContentType', '')
  if not file_name or not file_content_type:
    abort(400, 'Missing X-File-Name or X-File-ContentType headers.')

  metadata_encoding = request.headers.get('X-Metadata-Encoding', 'utf8')
  try:
    metadata = request.stream.read(metadata_length).decode(metadata_encoding)
  except UnicodeDecodeError as exc:
    abort(400, 'Could not decode metadata as {}'.format(metadata_encoding))

  try:
    metadata = json.loads(metadata)
    if not isinstance(metadata, dict):
      raise ValueError('expected JSON object')
  except ValueError as e:
    abort(400, 'Could not decode metadata as JSON ({})'.format(e))

  update_if_exists = check_bool_header('X-Update-If-Exists')
  # XXX Limit artifact upload size?

  # Open the write stream in the storage.
  try:
    wstream, uri = config.storage.open_write_file(loc, file_name, content_length)
  except storage.PermissionError as e:
    current_app.logger.exception(e)
    abort(500)

  with wstream, config.database.query_context():
    # Create an entry in the database.
    info = database.ObjectInfo(loc, metadata=metadata, filename=file_name,
        uri=uri, mime=file_content_type)
    try:
      is_new_object = config.database.create_object(info, update_if_exists)
    except database.LocationDoesNotExist as e:
      wstream.abort()
      return {'status': 'LocationDoesNotExist', 'at': str(e.location)}, 404
    except database.LocationAlreadyExists as e:
      wstream.abort()
      return {'status': 'LocationAlreadyExists', 'at': str(e.location)}, 409

    # Upload the data to the write stream.
    try:
      shutil.copyfileobj(request.stream, wstream)
    except storage.WriteOverflow as exc:
      return {'status': 'BadRequest', 'at': str(loc),
              'message': 'WriteOverflow -- received more data than specified in the request'}, 400

  status = 'Created' if is_new_object else 'Updated'
  return {'status': status, 'at': str(loc)}


@app.route('/info', methods=['GET'])
@jsonify()
@check_auth(config)
def info():
  perm = config.accesscontrol.get_permissions(database.Location(''), request.user_id)
  if not perm.can_read:
    abort(403)
  return {
    'numLevels': config.database.num_levels()
  }


@app.route('/location', methods=['GET'], strict_slashes=False)
@app.route('/location/<path:path>', methods=['GET', 'PUT', 'DELETE'])
@jsonify(cls=JsonEncoder)
@check_auth(config)
def location(path=''):
  ac = config.accesscontrol
  loc = database.Location(path)
  is_root = len(loc) == 0

  if len(loc) > config.database.num_levels():
    # Bad request because specified number of levels are not supported.
    return {'status': 'BadRequest', 'at': str(loc),
            'message': 'The location is not supported by the repository.'}, 400

  if not is_root and not config.storage.supports_location(loc):
    # Bad request because the storage doesn't support it.
    return {'status': 'BadRequest', 'at': str(loc),
            'message': 'The location is not supported by the repository.'}, 400

  perm = ac.get_permissions(loc, request.user_id)
  if not is_root and not perm.can_read:
    # Forbidden for PUT and DELETE requests.
    abort(404 if request.method == 'GET' else 403)

  is_object = len(loc) == config.database.num_levels()

  if request.method == 'DELETE':
    if is_root or not perm.can_delete:
      return {'status': 'PermissionDenied', 'at': str(loc)}, 403
    recursive_delete = check_bool_header('X-Recursive-Delete')
    try:
      with config.database.query_context():
        deleted_objects = config.database.delete_location(loc, recursive_delete)
    except database.LocationHasChildren as e:
      return {'status': 'LocationHasChildren', 'at': str(e.location)}, 409
    except database.LocationDoesNotExist as e:
      return {'status': 'LocationDoesNotExist', 'at': str(e.location)}, 404
    # Delete the storage for all deleted objects.
    for info in deleted_objects:
      try:
        config.storage.delete_file(info.location, info.filename, info.uri)
      except storage.FileDoesNotExist as e:
        # XXX log to proper logging facility
        print('[warning] On deleting object {}: File does not exist (URI {})'
            .format(info.location, info.uri))
      except Exception as e:
        current_app.logger.exception(e)
    return {'status': 'Deleted', 'at': str(loc)}

  if request.method == 'PUT':
    if is_root or not perm.can_write:
      return {'status': 'PermissionDenied', 'at': str(loc)}, 403
    if is_object:
      return _handle_put_object(loc)
    content_type = request.headers.get('Content-Type', '')
    if content_type and content_type != 'application/json':
      return {'status': 'BadRequest', 'at': str(loc),
              'message': 'Expected Content-Type: application/json, got {}'.format(content_type)}, 400
    if content_type:
      try:
        metadata = json.load(request.stream)
        if not isinstance(metadata, dict):
          raise ValueError('expected JSON object')
      except ValueError as e:
        return {'status': 'BadRequest', 'at': str(loc),
                'message': 'JSON payload could not be parsed ({})'.format(e)}, 400
    else:
      metadata = {}
    update_if_exists = check_bool_header('X-Update-If-Exists')
    info = database.LocationInfo(loc, metadata)
    try:
      with config.database.query_context():
        is_new_location = config.database.create_location(info, update_if_exists)
    except database.LocationDoesNotExist as e:
      return {'status': 'LocationDoesNotExist', 'at': str(e.location)}, 404
    except database.LocationAlreadyExists as e:
      return {'status': 'LocationAlreadyExists', 'at': str(e.location)}, 409
    status = 'Created' if is_new_location else 'Updated'
    return {'status': status, 'at': str(loc)}

  if request.method == 'GET':
    # XXX Return object information if this is an object location
    result = {'status': 'Result'}
    try:
      with config.database.query_context():
        key, data = get_location_as_json(loc)
      result[key] = data
    except database.LocationDoesNotExist as e:
      return {'status': 'LocationDoesNotExist'}, 404
    except database.InvalidLocationQuery as e:
      return {'status': 'BadRequest', 'at': str(e.location),
              'message': 'The location is not supported by the repository.'}, 400
    return result


@app.route('/read/<path:path>')
@check_auth(config)
def read(path):
  location = database.Location(path)
  if len(location) != config.database.num_levels():
    abort(404)

  with config.database.query_context():
    try:
      obj = next(config.database.list_objects(location))
    except StopIteration:
      abort(404)

  url = get_object_url(obj, default=None)
  if url is not None:
    return redirect(url)

  # XXX Support HTTP Range header?
  try:
    fp, size = config.storage.open_read_file(location, obj.filename, obj.uri)
  except storage.FileDoesNotExist:
    abort(404)
  response = send_file(fp, mimetype=obj.mime, as_attachment=True, attachment_filename=obj.filename)
  response.headers.add('Content-Length', str(size))
  return response
