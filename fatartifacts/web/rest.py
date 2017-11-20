
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
    return list(app.database.get_group_ids())


class ListArtifactIds(Resource):

  def get(self, group_id):
    return list(app.database.get_artifact_ids(group_id))


class ListVersions(Resource):

  def get(self, group_id, artifact_id):
    return list(app.database.get_artifact_versions(group_id, artifact_id))


class ListObjects(Resource):

  def get(self, group_id, artifact_id, version):
    result = {}
    for o in app.database.get_artifact_objects(group_id, artifact_id, version):
      url = get_object_url(group_id, artifact_id, version, o)
      result[o.tag] = {'filename': o.filename, 'url': url}
    return result


class Object(Resource):

  def get(self, group_id, artifact_id, version, tag):
    try:
      o = app.database.get_artifact_object(group_id, artifact_id, version, tag)
    except ArtifactDoesNotExist:
      abort(404)
    url = get_object_url(group_id, artifact_id, version, o)
    return {'tag': o.tag, 'filename': o.filename, 'url': url}

  def put(self, group_id, artifact_id, version, tag):
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
  fp = app.storage.open_read_file(group_id, artifact_id, version, tag, obj.filename)
  return send_file(fp, mimetype=obj.mime, as_attachment=True,
    attachment_filename=obj.filename)
