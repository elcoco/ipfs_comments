import logging
import sys
from pprint import pprint
from functools import wraps

from core import app
from core import plugin_manager
from core.messages import message

from core.exceptions import AuthException, AuthUserNotAddedError, AuthUserNotChangedError
from core.exceptions import UnauthorizedError, ForbiddenError, NotFoundError, BadRequestError, ConflictError, InternalServerError
from core.exceptions import BadRequestError

from flask import jsonify
from flask import request


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


@app.route("/sites/<site_id>/blogs/<blog_id>/posts/<post_id>/comments", methods=['GET'])
def get_comment(site_id, blog_id, post_id):

    # call plugins to create extra pages, eg: rss, site_map etc...
    res = plugin_manager.run_hook('get_post_comments', site_id, blog_id, post_id)

    #raise InternalServerError("disko", trace={"bla": "bla"})
    return message(payload=res)


@app.route("/sites/<site_id>/blogs/<blog_id>/posts/<post_id>/comments", methods=['POST'])
@requires_post_data
def add_comment(site_id, blog_id, post_id):
    print(site_id, blog_id, post_id, request.json)

    # call plugins to create extra pages, eg: rss, site_map etc...
    res = plugin_manager.run_hook('add_comment', site_id, blog_id, post_id, request.json)

    #raise InternalServerError("disko", trace={"bla": "bla"})
    return message(msg="Added comment", payload=res)
