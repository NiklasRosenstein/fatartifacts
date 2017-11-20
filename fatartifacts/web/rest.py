
from .fablueprint import FaBlueprint
from ..base.database import ArtifactDoesNotExist
from flask import abort, redirect, url_for, send_file
from flask_restful import Api, Resource

app = FaBlueprint(__name__, __name__)
api = Api(app)

# XXX Use app.accesscontrol to determine accessibility.
# XXX Implement creation/deletion of artifacts (with respect to app.accesscontrol).


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
    result = []
    for o in app.database.get_artifact_objects(group_id, artifact_id, version):
      if o.has_web_uri():
        url = o.uri
      else:
        url = url_for(__name__ + '.read',
          group_id=group_id, artifact_id=artifact_id, version=version,
          tag=o.tag)
      result.append({'tag': o.tag, 'filename': o.filename, 'url': url})
    return result


api.add_resource(ListGroupIds, '/list/')
api.add_resource(ListArtifactIds, '/list/<group_id>')
api.add_resource(ListVersions, '/list/<group_id>/<artifact_id>')
api.add_resource(ListObjects, '/list/<group_id>/<artifact_id>/<version>')


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
