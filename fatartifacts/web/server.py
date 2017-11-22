
from . import rest
from flask import Flask

app = Flask(__name__)
app.register_blueprint(rest.app)

import fatartifacts_server_config
rest.app.config = fatartifacts_server_config
