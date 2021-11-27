import logging
from pprint import pprint
from functools import wraps

from core import app, auth, config, plugin_manager, captcha
from core.messages import message

from core.exceptions import AuthException, AuthUserNotAddedError, AuthUserNotChangedError
from core.exceptions import UnauthorizedError, ForbiddenError, NotFoundError, BadRequestError, ConflictError, InternalServerError
from core.exceptions import BadRequestError

from core.auth import Auth

from flask import jsonify
from flask import request

# safety first ;)
from flask import escape

from flask_jwt_extended import jwt_required, get_jwt_identity 

logger = logging.getLogger('app')

# handle error messages
@app.errorhandler(UnauthorizedError)
@app.errorhandler(ForbiddenError)
@app.errorhandler(NotFoundError)
@app.errorhandler(BadRequestError)
@app.errorhandler(ConflictError)
@app.errorhandler(InternalServerError)
def handle_error(error):
    return jsonify(error.to_dict()), error.status_code

def require_post_data(func):
    """ Raise BadRequestError if no post data is given """
    @wraps(func)
    def inside(*args, **kwargs):
        if request.json == None:
            raise BadRequestError("No post data")
        return func(*args, **kwargs)
    return inside


class APIAuth():
    """ Enable login, return access token if user exists
        Only return UnauthorizedError, we don't want to give any hints to 1337 h4x0rs """
    def post_login(self):
        try:
            username = request.json["username"]
            password = request.json["password"]
        except Exception as e:
            # NOTE yes yes, bad practice I know, but necessary in this case.
            # always return UnauthorizedError in case of any error for safety.
            # make sure to not give any identification of the error to the user.
            logger.error(f"Auth error: {e}")
            raise UnauthorizedError

        user = auth.user_exists(username)
        if not user:
            logger.error(f"Failed authentication attempt for non existing user: {username}")
            raise UnauthorizedError

        if auth.verify_password(username, password):
            return message(payload={"access_token" : auth.get_user_token(username, config["core"]["user_token_expiration_days"])})
        else:
            logger.error(f"Failed authentication attempt for user, wrong password: {username}")
            raise UnauthorizedError


class APIUser():
    @jwt_required()
    @auth.require_admin_identity
    def get_users(self):
        """ Don't send password hashes """
        users = []
        for user in config['core']['users']:
            user["password"] = "secret"
            users.append(user)
        return message(payload=users)

    @jwt_required()
    @auth.require_admin_identity
    def get_user(self, username):
        user = auth.user_exists(username)
        if not user:
            raise ConflictError("Failed get user")
        else:
            return message(payload=user)

    @jwt_required()
    @auth.require_admin_identity
    @require_post_data
    def post_user(self):
        try:
            password = request.json["password"]
            username = request.json["username"]
            admin = request.json.get("admin", False)
        except KeyError as e:
            raise BadRequestError(f"Missing required attributes", trace=e)
        except TypeError as e:
            raise BadRequestError(f"Wrong type", trace=e)

        if auth.user_exists(username):
            raise ConflictError("Failed to create user")

        user = auth.add_user(username, password, admin=admin)
        return message(msg=f"Successfully created user: {username}", payload=user)

    @jwt_required()
    @auth.require_admin_identity
    def put_user(self, username):
        try:
            password = request.json["password"]
            admin = request.json.get("admin", False)
        except KeyError as e:
            raise BadRequestError(f"Missing required attributes", trace=e)
        except TypeError as e:
            raise BadRequestError(f"Wrong type", trace=e)

        if not auth.user_exists(username):
            raise ConflictError("Failed to update user")

        try:
            user = auth.add_user(username, password, admin)
        except AuthUserNotChangedError as e:
            raise ConflictError("Failed to create user", trace=e)

        return message(msg=f"Successfully updated user: {username}", payload=user)

    @jwt_required()
    @auth.require_admin_identity
    def delete_user(self, username):
        if not auth.user_exists(username):
            raise ConflictError("Failed to delete user")

        user = auth.del_user(username)
        return message(msg=f"Successfully deleted user: {username}", payload=user)


class APIComments():
    def sort_comments(self, comments, _id=None, level=0):
        ret = []

        cur_level = [c for c in comments if not c["replyTo"] or c["replyTo"] == _id]

        for c in cur_level:

            cs = [x for x in comments if x not in cur_level]
            ret.append(self.sort_comments(cs, c["id"], level+1))

        return ret

    def print_comments(self, comments, spacing=0):
        space = ' ' * spacing

        for c in comments:
            pass


    def get_comments(self, page_id):
        # call plugins manager
        res = plugin_manager.run_hook('get_comments', page_id)
        return message(payload=res)
        #return message(payload=self.sort_comments(res))

    @require_post_data
    @captcha.require_captcha
    def post_comment(self, page_id):
        # escape data for safety and stuff
        try:
            comment = request.json["comment"]
            comment["author"] = escape(comment["author"])
            comment["content"] = escape(comment["content"])
            comment["replyTo"] = escape(comment["replyTo"])
        except KeyError as e:
            print(f"Missing keys: {e}")
            raise BadRequestError(f"Missing keys: {e}")
        print(comment)

        if not (comment['author'] and comment['content']):
            raise BadRequestError(f"Missing values")

        res = plugin_manager.run_hook('add_comment', page_id, comment)

        return message(msg="Added comment", payload=res)


class APICaptcha():
    def get_captcha(self):
        challenge = captcha.get_challenge()
        return message(msg="captcha", payload={"id": challenge.uuid,
                                               "challenge": challenge.challenge})
