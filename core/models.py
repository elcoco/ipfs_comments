#!/usr/bin/env python3

import datetime

from sqlalchemy.sql import func
from sqlalchemy.ext.hybrid import hybrid_property

from core import db


class User(db.Model):
    #__tablename__ = 'users'
    user_id = db.Column(db.Integer, primary_key=True, nullable=False)

    # name is the more recognizable name, could be company name or whatever
    username = db.Column(db.String(120), unique=True, nullable=False)

    email = db.Column(db.String(120), nullable=True)

    first_name = db.Column(db.String(120), nullable=True)
    last_name = db.Column(db.String(120), nullable=True)
    password = db.Column(db.String(120), nullable=False)

    # tell the sql server to create a timestamp at creation/onupdate
    date_created = db.Column(db.DateTime(timezone=True), server_default=func.now())
    date_modified = db.Column(db.DateTime(timezone=True), server_default=func.now(), server_onupdate=func.now())

    # indicate whether user has admin privileges
    admin = db.Column(db.Boolean(), default=False)

    # the app ids the user is allowed to post data to, an admin is allowed to post to all app ids
    app_ids = db.Column(db.String(1000), nullable=True)

    def serialize(self):
        data = {}
        data["user_id"] = self.user_id
        data["username"] = self.username
        data["email"] = self.email
        data["password"] = self.password
        data["admin"] = self.admin
        data["app_ids"] = self.app_ids
        return data

    def __repr__(self):
        return str(self.serialize())
