import logging
from passlib.hash import sha256_crypt

#from core.auth import Auth

from flask_sqlalchemy import SQLAlchemy, BaseQuery

from core.exceptions import NotFoundError, InternalServerError, AuthException, AuthUserNotAddedError
from sqlalchemy.exc import SQLAlchemyError


logger = logging.getLogger('app')


class CustomBaseQuery(BaseQuery):
    """ This supernice subclass of BaseQuery extends the *_or_404 methods
        to return a custom error message when no value is found in the database"""
    def get_or_404(self, ident):
        try:
            row = self.get(ident)
        except SQLAlchemyError as e:
            raise InternalServerError("Failed to query database")

        if row:
            return row
        logger.info(f"Attribute not found in database: {ident}")
        raise NotFoundError(f"Attribute not found in database: {ident}")

    def first_or_404(self):
        try:
            row = self.first()
        except SQLAlchemyError as e:
            raise InternalServerError("Failed to query database")

        if row:
            return row
        logger.info(f"Attribute not found in database")
        raise NotFoundError(f"Attribute not found in database")

def get_password_hash(password):
    return sha256_crypt.encrypt(password)

def add_admin_user(username, password, db):
    from core.models import User
    admin_user = User()

    db.session.add(admin_user)
    try:
        # create row in SQL user table
        db.session.commit()
        logger.info("Added admin user to database")
        return True
    except SQLAlchemyError as e:
        print("Failed to add admin user to database")
        print(e)


def init_db(db, admin_username, admin_password):
    from core.models import User

    db.create_all()
    logger.info("Created database...")

    user = User.query.filter_by(username=admin_username).first()
    print(user)
    if not user:
        print("Created new admin user")
        user = User()
    else:
        print("Updated admin user")

    user.username = admin_username
    user.password = get_password_hash(str(admin_password))
    user.admin = True
    print(">>>>>>>>>>", user)

    db.session.add(user)

    try:
        db.session.commit()
        #return user
    except SQLAlchemyError as e:
        raise AuthUserNotAddedError(e)

    #print(flush=True)
    #print(50*"=", flush=True)
    #print("Created sqlite database, and admin user", flush=True)
    #print(f"username: {admin_username}", flush=True)
    #print(f"password: {admin_password}", flush=True)
    #print(50*"=", flush=True)
    #print(flush=True)
