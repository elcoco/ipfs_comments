#!/usr/bin/env python3

from core import app
from core import api
from core.api import APIAuth, APIUser, APIComments


auth_resource = APIAuth()
users_resource = APIUser()
comments_resource = APIComments()

prefix = "/v0.1"
app.add_url_rule(f"{prefix}/auth", view_func=auth_resource.post_login, methods=["POST"])

app.add_url_rule(f"{prefix}/users", view_func=users_resource.get_users, methods=["GET"])
app.add_url_rule(f"{prefix}/users/<user_id>", view_func=users_resource.get_user, methods=["GET"])
app.add_url_rule(f"{prefix}/users/<user_id>", view_func=users_resource.delete_user, methods=["DELETE"])
app.add_url_rule(f"{prefix}/users", view_func=users_resource.post_user, methods=["POST"])
app.add_url_rule(f"{prefix}/users/<user_id>", view_func=users_resource.put_user, methods=["PUT"])

app.add_url_rule(f"{prefix}/sites/<site_id>/blogs/<blog_id>/posts/<post_id>/comments", view_func=comments_resource.get_comments, methods=["GET"])
app.add_url_rule(f"{prefix}/sites/<site_id>/blogs/<blog_id>/posts/<post_id>/comments", view_func=comments_resource.post_comment, methods=["POST"])

# only for development purposes
def run():
    app.run(debug=True, host='0.0.0.0')
