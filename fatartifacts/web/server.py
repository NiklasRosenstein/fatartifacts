
from . import rest
from flask import Flask

app = Flask(__name__)
app.register_blueprint(rest.app)

import fatartifacts_server_config as cfg
rest.app.init_fa_connectors(cfg.accesscontrol, cfg.database, cfg.storage)
