"""
This code was provided as example in flask-jwt-extended and it is used in DeQua
with slight modifications.
https://github.com/vimalloc/flask-jwt-extended/blob/master/examples/database_blacklist/blacklist_helpers.py
"""
from datetime import datetime, timezone, timedelta
#from exceptions import TokenNotFound

from sqlalchemy.orm.exc import NoResultFound
from flask_jwt_extended import decode_token, create_access_token
import pdb
#pdb.set_trace()
from app.models import Token
from app import db


def _epoch_utc_to_datetime(epoch_utc):
    """
    Helper function for converting epoch timestamps (as stored in JWTs) into
    python datetime objects (which are easier to use with sqlalchemy).
    """
    return datetime.fromtimestamp(epoch_utc, tz=timezone.utc)


def generate_token_for_user(user, token_type='base', expiration=timedelta(minutes=10)):
    """
    Generate a valid token for a user. It is possible to specify the token type
    and the validity time of the token.
    """
    token = create_access_token(identity=user.id,
                                user_claims={'type': token_type},
                                expires_delta=expiration)
    add_token_to_database(token, user)
    return token


def add_token_to_database(encoded_token, user):
    """
    Adds a new token to the database. It is not revoked when it is added.
    :param identity_claim:
    """
    decoded_token = decode_token(encoded_token)
    jti = decoded_token['jti']
    token_type = decoded_token['user_claims']['type']
    if 'exp' in decoded_token:
        expires = _epoch_utc_to_datetime(decoded_token['exp'])
    else:
        expires = None
    revoked = False

    db_token = Token(
        token=encoded_token,
        jti=jti,
        token_type=token_type,
        user=user,
        expires=expires,
        revoked=revoked,
    )
    db.session.add(db_token)
    db.session.commit()


def is_token_revoked(decoded_token):
    """
    Checks if the given token is revoked or not. Because we are adding all the
    tokens that we create into this database, if the token is not present
    in the database we are going to consider it revoked, as we don't know where
    it was created.
    """
    jti = decoded_token['jti']
    try:
        token = Token.query.filter_by(jti=jti).one()
        return token.revoked
    except NoResultFound:
        return True


def get_user_tokens(user):
    """
    Returns all of the tokens, revoked and unrevoked, that are stored for the
    given user
    """
    return Token.query.filter_by(user=user).all()


def revoke_token(token_id, user):
    """
    Revokes the given token. Raises a TokenNotFound error if the token does
    not exist in the database
    """
    try:
        token = Token.query.filter_by(id=token_id, user=user).one()
        token.revoked = True
        db.session.commit()
    except NoResultFound:
        raise TokenNotFound("Could not find the token {}".format(token_id))


def unrevoke_token(token_id, user):
    """
    Unrevokes the given token. Raises a TokenNotFound error if the token does
    not exist in the database
    """
    try:
        token = Token.query.filter_by(id=token_id, user=user).one()
        token.revoked = False
        db.session.commit()
    except NoResultFound:
        raise TokenNotFound("Could not find the token {}".format(token_id))


def prune_database():
    """
    Delete tokens that have expired from the database.
    How (and if) you call this is entirely up you. You could expose it to an
    endpoint that only administrators could call, you could run it as a cron,
    set it up with flask cli, etc.
    """
    now = datetime.now()
    expired = Token.query.filter(Token.expires < now).all()
    for token in expired:
        db.session.delete(token)
    db.session.commit()

class TokenNotFound(Exception):
    """
    Indicates that a token could not be found in the database
    """
    pass
