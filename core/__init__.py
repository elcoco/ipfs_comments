import secrets
import string
from pathlib import Path
import sys

from core.plugin_manager import PluginManager
from core.plugin_manager import Policy
from core.config import Config
from core.utils import CustomBaseQuery, init_db

from flask import Flask, jsonify
from flask_jwt_extended import JWTManager
from flask_sqlalchemy import SQLAlchemy 

#from core.auth import Auth


def gen_password(length=20):
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for i in range(length))

# init config file
config = Config()
config.set_path(Path(__file__).parent.parent / 'config.yml')

config['core'] = {}
config['core']['plugins_enabled'] = ['ipfs']
config['core']['plugins_enabled'] = ['ipfs']
config["core"]["jwt_secret_key"] = gen_password()
config["core"]["user_token_expiration_days"] = 1000000
config["core"]["sensor_token_expiration_days"] = 1000000
config["core"]["admin"] = {}
config["core"]["admin"]["username"] = "admin"
config["core"]["admin"]["password"] = gen_password()
config['plugins'] = {}
config['sqlite'] = {}
config['sqlite']['path'] = str((Path(__file__).parent.parent / 'db.sqlite').absolute())
config['plugins']['ipfs'] = {}
config['plugins']["ipfs"]["root_cid"] = ''

#config["core"]["users"] = []
#admin_user = {}
#admin_user["username"] = "admin"
#admin_user["password"] = gen_password()
#config["core"]["users"].append(admin_user)

if not config.configfile_exists():
    config.write(commented=False)

config.load(merge=False)


# handles plugins and plugin hooks
plugin_manager = PluginManager()

# add plugin manager hooks that plugins can subscribe to
plugin_manager.register_hook('add_comment', run_policy=Policy.FIRST)
plugin_manager.register_hook('get_comments', run_policy=Policy.FIRST)

# initialize plugins, this also adds the plugin templates path to jinja2 env
plugin_manager.load_plugins(['ipfs'])

# init flask
app = Flask(__name__)


# Setup flask_jwt_extended
app.config['JWT_SECRET_KEY'] = config["core"]["jwt_secret_key"]
jwt = JWTManager(app)

# custom JWT error message on expired token, should probably be placed somewhere else
@jwt.expired_token_loader
def my_expired_token_callback(expired_token):
    token_type = expired_token['type']
    return jsonify({ "error" : { "code" : 401, "message" : "Token has expired" } }), 401

# Database
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{config["sqlite"]["path"]}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Init db
db = SQLAlchemy(app, query_class=CustomBaseQuery)

init_db(db,
        config["core"]["admin"]["username"],
        config["core"]["admin"]["password"])
