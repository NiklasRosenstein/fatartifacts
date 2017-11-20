
from .auth import AuthorizationError
from .fablueprint import FaBlueprint
from ..base.database import ArtifactDoesNotExist, ArtifactAlreadyExists, ArtifactObject
from flask import abort, redirect, request, url_for, send_file, Response
from werkzeug.exceptions import HTTPException
import functools
import json
import shutil

app = FaBlueprint(__name__, __name__)

# XXX Use app.accesscontrol to determine accessibility.
# XXX Implement creation/deletion of artifacts (with respect to app.accesscontrol).

def get_object_url(group_id, artifact_id, version, obj):
  if obj.has_web_uri():
    return obj.uri
  return url_for(__name__ + '.read',
    group_id=group_id, artifact_id=artifact_id, version=version, tag=obj.tag)


def jsonify(func):
  @functools.wraps(func)
  def wrapper(*args, **kwargs):
    try:
      result = func(*args, **kwargs)
      return Response(json.dumps(result), status=200, mimetype='text/json')
    except HTTPException as e:
      return Response(json.dumps({
        'message': str(e)
      }), status=e.code, mimetype='text/json')
    except Exception as e:
      return Response(json.dumps({
        'message': 'The server has encountered an internal server error.'
      }), status=500, mimetype='text/json')

  return wrapper


def close_input_stream(func):
  @functools.wraps(func)
  def wrapper(*a, **kw):
    try:
      return func(*a, **kw)
    finally:
      fp = request.environ.get('wsgi.input')
      if fp:
        fp.close()
  return wrapper


@app.route('/', methods=['GET'])
@jsonify
def list_groups():
  ac = app.accesscontrol
  return [
    group_id for group_id in app.database.get_group_ids()
    if ac.get_group_permissions(request.user_id, group_id).can_read
  ]


@app.route('/<group_id>', methods=['GET'])
@jsonify
def list_artifacts(group_id):
  ac = app.accesscontrol
  if not ac.get_group_permissions(request.user_id, group_id).can_read:
    abort(404)
  return [
    artifact_id for artifact_id in app.database.get_artifact_ids(group_id)
    if ac.get_artifact_permissions(request.user_id, group_id, artifact_id).can_read
  ]


@app.route('/<group_id>/<artifact_id>', methods=['GET'])
@jsonify
def list_versions(group_id, artifact_id):
  if not app.accesscontrol.get_artifact_permissions(request.user_id, group_id, artifact_id).can_read:
    abort(404)
  return list(app.database.get_artifact_versions(group_id, artifact_id))


@app.route('/<group_id>/<artifact_id>/<version>', methods=['GET'])
@jsonify
def list_objects(group_id, artifact_id, version):
  if not app.accesscontrol.get_artifact_permissions(request.user_id, group_id, artifact_id).can_read:
    abort(404)
  result = {}
  for o in app.database.get_artifact_objects(group_id, artifact_id, version):
    url = get_object_url(group_id, artifact_id, version, o)
    result[o.tag] = {'filename': o.filename, 'url': url}
  return result


@app.route('/<group_id>/<artifact_id>/<version>/<tag>', methods=['GET', 'PUT', 'DELETE'])
@jsonify
def handle_object(group_id, artifact_id, version, tag):

  def get():
    if not app.accesscontrol.get_artifact_permissions(request.user_id, group_id, artifact_id).can_read:
      abort(404)
    try:
      o = app.database.get_artifact_object(group_id, artifact_id, version, tag)
    except ArtifactDoesNotExist:
      abort(404)
    url = get_object_url(group_id, artifact_id, version, o)
    return {'tag': o.tag, 'filename': o.filename, 'url': url}

  @close_input_stream
  def put():
    if not app.accesscontrol.get_artifact_permissions(request.user_id, group_id, artifact_id).can_write:
      abort(403)

    mime = request.headers.get('Content-Type')
    if not mime:
      abort(400, 'Missing Content-Type header.')
    filename = request.headers.get('Content-Name')
    if not filename:
      abort(400, 'Missing Content-Name header.')

    dst, uri = app.storage.open_write_file(group_id, artifact_id, version, tag, filename)

    # XXX Check write permissions.
    # XXX Limit artifact upload size?
    with dst:
      # Ensure that there is some data incoming.
      data = request.stream.read(1024)
      if not data:
        abort(400, 'No data received.')
      dst.write(data)

      # Create an entry in the database.
      try:
        obj = ArtifactObject(tag, filename, uri, mime)
        app.database.create_artifact(group_id, artifact_id, version, obj)
      except ArtifactAlreadyExists as exc:
        abort(400, 'Object {} already exists.'.format(exc))

      # Copy the rest of the data.
      shutil.copyfileobj(request.stream, dst)

    return {'message': "Object {}:{}:{}:{} created.".format(group_id, artifact_id, version, tag)}

  def delete():
    if not app.accesscontrol.get_artifact_permissions(request.user_id, group_id, artifact_id).can_delete:
      abort(403)

    try:
      obj = app.database.delete_artifact(group_id, artifact_id, version, tag)
    except ArtifactDoesNotExist:
      abort(404)

    app.storage.delete_file(group_id, artifact_id, version, tag, obj.filename, obj.uri)
    return {'message': "Object {}:{}:{}:{} deleted.".format(group_id, artifact_id, version, tag)}

  if request.method == 'GET':
    return get()
  elif request.method == 'PUT':
    return put()
  elif request.method == 'DELETE':
    return delete()
  else:
    flask.abort(403)


@app.route('/read/<group_id>/<artifact_id>/<version>/<tag>')
def read(group_id, artifact_id, version, tag):
  try:
    obj = app.database.get_artifact_object(group_id, artifact_id, version, tag)
  except ArtifactDoesNotExist:
    abort(404)
  if obj.has_web_uri():
    return redirect(obj.uri)
  # XXX Support HTTP Range header?
  fp = app.storage.open_read_file(group_id, artifact_id, version, tag, obj.filename, obj.uri)
  return send_file(fp, mimetype=obj.mime, as_attachment=True,
    attachment_filename=obj.filename)


@app.before_request
def before_request():
  try:
    request.user_id = app.auth.do_authorization(request)
  except AuthorizationError as exc:
    abort(403, str(exc))
