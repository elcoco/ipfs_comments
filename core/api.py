import logging
import sys
from pprint import pprint
from functools import wraps

from core import app
from core import config
from core import plugin_manager
from core.messages import message

from core.exceptions import AuthException, AuthUserNotAddedError, AuthUserNotChangedError
from core.exceptions import UnauthorizedError, ForbiddenError, NotFoundError, BadRequestError, ConflictError, InternalServerError
from core.exceptions import BadRequestError

from core.auth import Auth

from core.models import User

from flask import jsonify
from flask import request

from flask_jwt_extended import jwt_required, get_jwt_identity 

# configure logging
formatter_info = logging.Formatter('%(message)s')
formatter_debug = logging.Formatter('%(levelname)5s %(module)3s.%(funcName)-10s %(lineno)3s %(message)s')
logger = logging.getLogger('app')
logger.setLevel(logging.DEBUG)
streamhandler = logging.StreamHandler(sys.stdout)
streamhandler.setLevel(logging.DEBUG)
logger.addHandler(streamhandler)

logger.setLevel(logging.DEBUG)
streamhandler.setFormatter(formatter_debug)

# handle error messages
@app.errorhandler(UnauthorizedError)
@app.errorhandler(ForbiddenError)
@app.errorhandler(NotFoundError)
@app.errorhandler(BadRequestError)
@app.errorhandler(ConflictError)
@app.errorhandler(InternalServerError)
def handle_error(error):
    return jsonify(error.to_dict()), error.status_code


def requires_post_data(func):
    """ Raise BadRequestError if no post data is given """
    @wraps(func)
    def inside(*args, **kwargs):
        if request.json == None:
            raise BadRequestError("No post data")
        return func(*args, **kwargs)
    return inside

def check_admin_identity(func):
    """ Decorator function that checks if token identity corresponds
        with an admin user id from the database """
    @wraps(func)
    def inside(*args, **kwargs):
        try:
            user_id = get_jwt_identity()["user_id"]
        except KeyError as e:
            logger.error(f"Unauthorized: failed to get JWT identity")
            raise UnauthorizedError
        except TypeError as e:
            logger.error(f"Unauthorized: failed to get JWT identity")
            raise UnauthorizedError
        else:
            if not User.query.filter_by(user_id=user_id, admin=True).first():
                logger.error(f"Unauthorized: user {user_id} is not an admin")
                raise UnauthorizedError
            return func(*args, **kwargs)
    return inside

def check_appid_permissions(func):
    """ Decorator function that checks if token identity corresponds
        with a user id from the database, and if this user_id had access
        rights to the app_id """
    @wraps(func)
    def inside(*args, **kwargs):
        try:
            user_id = get_jwt_identity()["user_id"]
        except KeyError as e:
            logger.error(f"Unauthorized: failed to get JWT identity")
            raise UnauthorizedError
        except TypeError as e:
            logger.error(f"Unauthorized: failed to get JWT identity")
            raise UnauthorizedError
        else:
            # admin may always post
            if not User.query.filter_by(user_id=user_id, admin=True).first():

                # try to get app_id from request
                try:
                    app_id = request.json["app_id"]
                except KeyError as e:
                    logger.error(f"Failed login attempt for user {user.username} with id {user.user_id}: no app_id in request")
                    raise UnauthorizedError
                except TypeError as e:
                    logger.error(f"Failed login attempt for user {user.username} with id {user.user_id}: no app_id in request")
                    raise UnauthorizedError
                else:
                    if app_id == None:
                        logger.error(f"Failed login attempt for user {user.username} with id {user.user_id}: no app_id in request")
                        raise UnauthorizedError(f"Missing app_id in body")

                user = User.query.get_or_404(user_id)

                # try to match app_id from request to the access rights of user. remove whitespace and stuff
                try:
                    user_app_ids = [x.strip() for x in user.app_ids.split(',')]
                except AttributeError as e:
                    logger.error(f"Failed login attempt for user {user.username} with id {user.user_id}: insufficient rights on app_id: {app_id}")
                    raise UnauthorizedError
                else:
                    if not app_id in user_app_ids:
                        logger.error(f"Failed login attempt for user {user.username} with id {user.user_id}: insufficient rights on app_id: {app_id}")
                        raise UnauthorizedError

            return func(*args, **kwargs)
    return inside


class APIAuth(Auth):
    """ Enable login, return access token if user exists
        Only return UnauthorizedError, we don't want to give any hints to 1337 h4x0rs """
    def post_login(self):
        try:
            username = request.json["username"]
            password = request.json["password"]
        except KeyError as e:
            raise UnauthorizedError
        except TypeError as e:
            raise UnauthorizedError
        except:
            # always return UnauthorizedError in case of any error for safety.
            # make sure to not give any identification of the error to the user.
            raise UnauthorizedError

        user = self.user_exists(username=username)
        if not user:
            logger.error(f"Failed authentication attempt for non existing user: {username}")
            raise UnauthorizedError

        if self.verify_password(username, password):
            return message(payload={"access_token" : self.get_user_token(user, config["core"]["user_token_expiration_days"])})
        else:
            logger.error(f"Failed authentication attempt for user, wrong password: {username}")
            raise UnauthorizedError


class APIUser(Auth):
    @jwt_required()
    @check_admin_identity
    def get_users(self):
        users = User.query.all()
        data = [x.serialize() for x in users]
        return message(payload=data)

    @jwt_required()
    @check_admin_identity
    def get_user(self, user_id):
        user = User.query.get_or_404(user_id)
        return message(payload=user.serialize())

    @jwt_required()
    @check_admin_identity
    @requires_post_data
    def post_user(self):
        try:
            request.json["password"]
            request.json["username"]
        except KeyError as e:
            raise BadRequestError(f"Missing required attributes", trace=e)
        except TypeError as e:
            raise BadRequestError(f"Wrong type", trace=e)

        try:
            user = self.add_user(dict(request.json))
        except AuthUserNotAddedError as e:
            raise ConflictError("Failed to create user", trace=e)

        return message(msg=f"Successfully created user: {user.user_id} and InfluxDB database", payload=user.serialize())

    @jwt_required()
    @check_admin_identity
    def put_user(self, user_id):
        user = User.query.get_or_404(user_id)

        try:
            user = self.update_user(user, dict(request.json))
        except AuthUserNotChangedError as e:
            raise ConflictError("Failed to create user", trace=e)

        return message(msg=f"Successfully updated user: {user.user_id}", payload=user.serialize())

    @jwt_required()
    @check_admin_identity
    def delete_user(self, user_id):
        user = User.query.get_or_404(user_id)
        db.session.delete(user)
        try:
            db.session.commit()
        except SQLAlchemyError as e:
            raise ConflictError(f"Failed to delete user: {user_id}", trace=e)

        return message(msg=f"Successfully deleted user: {user.user_id}", payload=user.serialize())


class APIComments():
    def get_comments(self, site_id, blog_id, post_id):

        # call plugins to create extra pages, eg: rss, site_map etc...
        res = plugin_manager.run_hook('get_comments', site_id, blog_id, post_id)

        #raise InternalServerError("disko", trace={"bla": "bla"})
        return message(payload=res)

    @jwt_required()
    @requires_post_data
    def post_comment(self, site_id, blog_id, post_id):

        # call plugins to create extra pages, eg: rss, site_map etc...
        res = plugin_manager.run_hook('add_comment', site_id, blog_id, post_id, request.json)

        #raise InternalServerError("disko", trace={"bla": "bla"})
        return message(msg="Added comment", payload=res)
