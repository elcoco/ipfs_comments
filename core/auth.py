#!/usr/bin/env python3

import logging
import datetime
from typing import Callable, Optional
from passlib.hash import sha256_crypt
from functools import wraps

from core.exceptions import AuthUserNotFoundError, AuthUserNotAddedError, AuthUserNotChangedError, UnauthorizedError

from flask_jwt_extended import create_access_token, get_jwt_identity 

logger = logging.getLogger('app')


class Auth():
    def __init__(self, config):
        self._config = config
        self._db = config["core"]["users"]

    def require_admin_identity(self, func: Callable):
        """ Decorator function that checks if token identity corresponds
            with an admin user id from the database """
        @wraps(func)
        def inside(*args, **kwargs):
            try:
                username = get_jwt_identity()["username"]
            except KeyError as e:
                logger.error(f"Unauthorized: failed to get JWT identity")
                raise UnauthorizedError
            except TypeError as e:
                logger.error(f"Unauthorized: failed to get JWT identity")
                raise UnauthorizedError
            else:
                if not self.user_is_admin(username):
                    logger.error(f"Unauthorized: user {username} is not an admin")
                    raise UnauthorizedError
                return func(*args, **kwargs)
        return inside

    def verify_password(self, username: str, password: str) -> Optional[bool]:
        user = self.user_exists(username)
        if user:
            return sha256_crypt.verify(password, user['password'])

    def get_password_hash(self, password: str) -> str:
        return sha256_crypt.hash(password)

    def user_exists(self, username: str) -> dict:
        try:
            return next(iter([u for u in self._db if u['username'] == username]))
        except StopIteration:
            logger.error(f"User {username} not found")

    def user_is_admin(self, username: str) -> Optional[dict]:
        try:
            return next(iter([u for u in self._db if u['username'] == username and u['admin']]))
        except KeyError:
            logger.error(f"User {username} not admin")
        except StopIteration:
            logger.error(f"User {username} not found")

    def add_user(self, username: str, password: str, admin: bool=False):
        """ Create/update user """
        user = self.user_exists(username)
        if not user:
            user = {}
            self._db.append(user)

        user["username"] = username
        user["password"] = self.get_password_hash(password)
        user["admin"] = admin

        self._config.write()
        return user

    def del_user(self, username: str):
        user = self.user_exists(username)
        self._db.remove(user)
        self._config.write()
        return user

    def get_token(self, identity: str, token_expiration_days: int=1000000):
        return create_access_token(identity=identity, expires_delta=datetime.timedelta(days=int(token_expiration_days)))

    def get_user_token(self, username: str, token_expiration_days: int=1000000):
        identity_json = {"username": username}
        return self.get_token(identity_json, token_expiration_days=int(token_expiration_days))
