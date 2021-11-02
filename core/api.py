import logging
import sys

from core import app
from core import plugin_manager
from core.messages import message

from core.exceptions import AuthException, AuthUserNotAddedError, AuthUserNotChangedError
from core.exceptions import UnauthorizedError, ForbiddenError, NotFoundError, BadRequestError, ConflictError, InternalServerError

from flask import jsonify
from flask import request


# configure logging
formatter_info = logging.Formatter('%(message)s')
formatter_debug = logging.Formatter('%(levelname)5s %(module)3s.%(funcName)-10s %(lineno)3s %(message)s')
logger = logging.getLogger('')
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

@app.route("/sites/<site_id>/blogs/<blog_id>/posts/<post_id>/comments", methods=['GET'])
def get_comment(site_id, blog_id, post_id):
    print(site_id, blog_id, post_id, request.json)

    # call plugins to create extra pages, eg: rss, site_map etc...
    plugin_manager.run_hook('get_comments', site_id, blog_id, post_id)

    raise InternalServerError("disko", trace={"bla": "bla"})
    #return message("Hello, World!")
