from core.plugin_manager import PluginManager
from core.plugin_manager import Policy

from flask import Flask, jsonify
from flask_jwt_extended import JWTManager
from flask_sqlalchemy import SQLAlchemy 


# handles plugins and plugin hooks
plugin_manager = PluginManager()

# add plugin manager hooks that plugins can subscribe to
plugin_manager.register_hook('add_comment', run_policy=Policy.FIRST)
plugin_manager.register_hook('get_post_comments', run_policy=Policy.FIRST)

# initialize plugins, this also adds the plugin templates path to jinja2 env
plugin_manager.load_plugins(['ipfs'])

# init flask
app = Flask(__name__)

# Setup flask_jwt_extended
app.config['JWT_SECRET_KEY'] = 'abcdefgh12345677'
#app.config['JWT_SECRET_KEY'] = config["api"]["jwt_secret_key"]
jwt = JWTManager(app)

# custom JWT error message on expired token, should probably be placed somewhere else
@jwt.expired_token_loader
def my_expired_token_callback(expired_token):
    token_type = expired_token['type']
    return jsonify({ "error" : { "code" : 401, "message" : "Token has expired" } }), 401

# Database
#app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{config["sqlite"]["path"]}/db.sqlite'
#app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Init db
#db = SQLAlchemy(app, query_class=CustomBaseQuery)
