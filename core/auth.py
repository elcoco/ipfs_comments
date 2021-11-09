#!/usr/bin/env python3

import logging
import datetime

from passlib.hash import sha256_crypt
from flask_jwt_extended import create_access_token
from sqlalchemy.exc import SQLAlchemyError

from flask_jwt_extended import get_jwt_identity 

from core import db
from core.models import User
from core.exceptions import AuthUserNotFoundError, AuthUserNotAddedError, AuthUserNotChangedError
from core.utils import get_password_hash

logger = logging.getLogger('app')

class Auth():
    def verify_password(self, username, password):
        user = User.query.filter_by(username=username).first()
        return sha256_crypt.verify(password, user.password)

    def check_user_identity(self):
        """ Check if JWT token identity exists in user table, and if user has admin permissions """
        return User.query.filter_by(username=get_jwt_identity(), admin=True).first()

    def user_exists(self, username=False, user_id=False):
        if username:
            return User.query.filter_by(username=username).first()
        elif user_id:
            return User.query.get(user_id)

    def user_is_admin(self, username):
        return User.query.filter_by(username=username, admin=True).first()

    def add_user(self, data):
        """ create user from Dict """
        user = User()

        for k,v in data.items():
            if not hasattr(user, k):
                raise AuthUserNotAddedError(f"No such attribute: {k}")

            # TODO do some password testing
            if k == "password":
                v = get_password_hash(str(v))

            setattr(user, k, v)

        db.session.add(user)
        # create row in SQL user table
        try:
            db.session.commit()
            return user
        except SQLAlchemyError as e:
            raise AuthUserNotAddedError(e)

    def update_user(self, user, data):
        """ update user from Dict """
        for k,v in data.items():
            if not hasattr(user, k):
                raise AuthUserNotChangedError(f"Wrong type, {k} does not exist in table")

            # TODO do some password testing
            if k == "password":
                v = get_password_hash(str(v))

            setattr(user, k, v)

        try:
            db.session.commit()
            return user
        except SQLAlchemyError as e:
            raise AuthUserNotChangedError(e)

    def get_token(self, identity, token_expiration_days=1000000):
        return create_access_token(identity=identity, expires_delta=datetime.timedelta(days=int(token_expiration_days)))

    def get_user_token(self, user, token_expiration_days=1000000):
        identity_json = {"user_id" : user.user_id, "username": user.username}
        return self.get_token(identity_json, token_expiration_days=int(token_expiration_days))
