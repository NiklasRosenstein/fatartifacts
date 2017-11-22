
from . import html, rest
from flask import Flask
import fatartifacts_server_config as cfg

app = Flask(__name__)
app.register_blueprint(rest.app, url_prefix=cfg.rest_prefix)
app.register_blueprint(html.app, url_prefix=cfg.html_prefix)

html.app.config = cfg
rest.app.config = cfg
