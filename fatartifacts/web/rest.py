
from .fablueprint import FaBlueprint
from ..base.database import ArtifactDoesNotExist
from flask import abort, redirect, request, url_for, send_file
from flask_restful import Api, Resource

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
    src = request.files.get('file')
    if not src:
      abort(400)
    mime = request.data.get('mimetype')
    if not mime:
      abort(400)
    filename = secure_filename(src.name)
    dst, uri = app.storage.open_write_file(group_id, artifact_id, version, tag, filename)
    with dst:
      shutil.copyfileobj(src, dst)
      obj = ArtifactObject(tag, filename, uri, mime)
      app.database.create_artifact(group_id, artifact_id, version, obj)
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
