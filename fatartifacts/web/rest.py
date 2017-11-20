
from .auth import AuthorizationError
from .fablueprint import FaBlueprint
from ..base.database import ArtifactDoesNotExist, ArtifactAlreadyExists, ArtifactObject
from flask import abort, redirect, request, url_for, send_file
from flask_restful import Api, Resource
from werkzeug.utils import secure_filename
import shutil

app = FaBlueprint(__name__, __name__)
api = Api(app)

# XXX Use app.accesscontrol to determine accessibility.
# XXX Implement creation/deletion of artifacts (with respect to app.accesscontrol).

def get_object_url(group_id, artifact_id, version, obj):
  if obj.has_web_uri():
    return obj.uri
  return url_for(__name__ + '.read',
    group_id=group_id, artifact_id=artifact_id, version=version, tag=obj.tag)


class ListGroupIds(Resource):

  def get(self):
    ac = app.accesscontrol
    return [
      group_id for group_id in app.database.get_group_ids()
      if ac.get_group_permissions(request.user_id, group_id).can_read
    ]


class ListArtifactIds(Resource):

  def get(self, group_id):
    ac = app.accesscontrol
    return [
      artifact_id for artifact_id in app.database.get_artifact_ids(group_id)
      if ac.get_artifact_permissions(request.user_id, group_id, artifact_id).can_read
    ]


class ListVersions(Resource):

  def get(self, group_id, artifact_id):
    if not app.accesscontrol.get_artifact_permissions(request.user_id, group_id, artifact_id).can_read:
      abort(404)
    return list(app.database.get_artifact_versions(group_id, artifact_id))


class ListObjects(Resource):

  def get(self, group_id, artifact_id, version):
    if not app.accesscontrol.get_artifact_permissions(request.user_id, group_id, artifact_id).can_read:
      abort(404)
    result = {}
    for o in app.database.get_artifact_objects(group_id, artifact_id, version):
      url = get_object_url(group_id, artifact_id, version, o)
      result[o.tag] = {'filename': o.filename, 'url': url}
    return result


class Object(Resource):

  def get(self, group_id, artifact_id, version, tag):
    if not app.accesscontrol.get_artifact_permissions(request.user_id, group_id, artifact_id).can_read:
      abort(404)
    try:
      o = app.database.get_artifact_object(group_id, artifact_id, version, tag)
    except ArtifactDoesNotExist:
      abort(404)
    url = get_object_url(group_id, artifact_id, version, o)
    return {'tag': o.tag, 'filename': o.filename, 'url': url}

  def put(self, group_id, artifact_id, version, tag):
    if not app.accesscontrol.get_artifact_permissions(request.user_id, group_id, artifact_id).can_write:
      abort(403)

    mime = request.headers.get('Content-Type')
    if not mime:
      abort(400, 'Missing Content-Type header.')
    filename = request.headers.get('Content-Name')
    if not filename:
      abort(400, 'Missing Content-Name header.')

    dst, uri = app.storage.open_write_file(group_id, artifact_id, version, tag, secure_filename(filename))

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
        abort(400, 'Artifact {} already exists.'.format(exc))

      # Copy the rest of the data.
      shutil.copyfileobj(request.stream, dst)

    return {'message': "Artifact created."}

  def delete(self, group_id, artifact_id, version, tag):
    if not app.accesscontrol.get_artifact_permissions(request.user_id, group_id, artifact_id).can_delete:
      abort(403)

    try:
      obj = app.database.delete_artifact(group_id, artifact_id, version, tag)
    except ArtifactDoesNotExist:
      abort(404)

    app.storage.delete_file(group_id, artifact_id, version, tag, obj.filename, obj.uri)
    return {'message': 'Artifact deleted.'}


api.add_resource(ListGroupIds, '/')
api.add_resource(ListArtifactIds, '/<group_id>')
api.add_resource(ListVersions, '/<group_id>/<artifact_id>')
api.add_resource(ListObjects, '/<group_id>/<artifact_id>/<version>')
api.add_resource(Object, '/<group_id>/<artifact_id>/<version>/<tag>')


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
