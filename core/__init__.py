import secrets
import string
from pathlib import Path
import sys
import logging

from core.plugin_manager import PluginManager
from core.plugin_manager import Policy
from core.config import Config
from core.iplogger import IPLogger

from flask import Flask, jsonify
from flask_jwt_extended import JWTManager
from flask_cors import CORS

from core.auth import Auth
from core.captcha import Captcha

# configure logging #######################################################
formatter_info = logging.Formatter('%(message)s')
formatter_debug = logging.Formatter('%(levelname)5s %(module)3s.%(funcName)-10s %(lineno)3s %(message)s')
logger = logging.getLogger('app')
logger.setLevel(logging.DEBUG)
streamhandler = logging.StreamHandler(sys.stdout)
streamhandler.setLevel(logging.DEBUG)
logger.addHandler(streamhandler)
logger.setLevel(logging.DEBUG)
streamhandler.setFormatter(formatter_debug)


# init config file #######################################################
def gen_password(length=20):
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for i in range(length))

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
config['core']['users'] = []
config['core']['captcha'] = {}
config['core']['captcha']['ttl'] = 60*5 # seconds
config['core']['ip_logger'] = {}
config['core']['ip_logger']['min_interval'] = 5 # seconds
config['plugins'] = {}
config['plugins']['ipfs'] = {}
config['plugins']["ipfs"]["root_cid"] = ''
config['plugins']["ipfs"]["ipns_key"] = 'self'

if not config.configfile_exists():
    config.write(commented=False)

config.load(merge=False)

# logs ips so we can protect ourselves from DDOSing
ip_logger = IPLogger()

# handle captchas
captcha = Captcha(ttl=config['core']['captcha']['ttl'])

# handles plugins and plugin hooks ######################################
plugin_manager = PluginManager()

# add plugin manager hooks that plugins can subscribe to
plugin_manager.register_hook('add_comment', run_policy=Policy.FIRST)
plugin_manager.register_hook('get_comments', run_policy=Policy.FIRST)

# initialize plugins, this also adds the plugin templates path to jinja2 env
plugin_manager.load_plugins(['ipfs'])

# init flask
app = Flask(__name__)

# enable cors for all domains
CORS(app)


# Setup flask_jwt_extended #############################################
app.config['JWT_SECRET_KEY'] = config["core"]["jwt_secret_key"]
jwt = JWTManager(app)

# custom JWT error message on expired token, should probably be placed somewhere else
@jwt.expired_token_loader
def my_expired_token_callback(expired_token):
    token_type = expired_token['type']
    return jsonify({ "error" : { "code" : 401, "message" : "Token has expired" } }), 401


# user management #####################################################
auth = Auth(config)

# add admin user if specified in config
if config["core"].get("admin"):
    logger.debug("Updating admin user from config file")
    auth.add_user(config["core"]["admin"]["username"],
                  config["core"]["admin"]["password"],
                  admin = True)
