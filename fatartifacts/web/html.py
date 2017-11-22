
from .decorators import check_auth
import flask
import werkzeug.local

app = flask.Blueprint(__name__, __name__)
app.config = None
config = werkzeug.local.LocalProxy(lambda: app.config)


@app.route('/')
@check_auth(config)
def index():
  return flask.render_template('index.html')

