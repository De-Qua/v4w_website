"""
This code was provided as example in flask-jwt-extended and it is used in DeQua
with slight modifications.
https://github.com/vimalloc/flask-jwt-extended/blob/master/examples/database_blacklist/blacklist_helpers.py
"""
from datetime import datetime, timezone, timedelta
#from exceptions import TokenNotFound
from flask import request
from sqlalchemy.orm.exc import NoResultFound
from flask_jwt_extended import decode_token, create_access_token
import pdb
#pdb.set_trace()
from app.models import Tokens, TokenTypes
from app import db


def _epoch_utc_to_datetime(epoch_utc):
    """
    Helper function for converting epoch timestamps (as stored in JWTs) into
    python datetime objects (which are easier to use with sqlalchemy).
    """
    if epoch_utc:
        return datetime.fromtimestamp(epoch_utc, tz=timezone.utc)
    else:
        return None

def create_new_token(user, token_type='base', expiration=datetime.now()+timedelta(minutes=10)):
    if not expiration:
        expires_delta = False
    else:
        expires_delta = expiration - datetime.now()
    if type(token_type) is str:
        type_found = TokenTypes.query.filter_by(type=token_type).one_or_none()
    elif type(token_type) is TokenTypes:
        type_found = TokenTypes.query.filter_by(type=token_type.type).one_or_none()
    else:
        type_found = None
    if not type_found:
        return
    token = create_access_token(identity=user.id,
                                user_claims={'type': token_type.type}, # type --> livello del token, a cosa puo accedere
                                expires_delta=expires_delta) # quanto tempo dura prima che scada
    decoded_token = decode_token(token)
    token_info = {
        'token': token,
        'jti': decoded_token['jti'],
    }
    return token_info

def generate_token_for_user(user, token_type='base', expiration=timedelta(minutes=10)):
    """
    Generate a valid token for a user. It is possible to specify the token type
    and the validity time of the token.
    """
    if type(token_type) is str:
        type_found = TokenTypes.query.filter_by(type=token_type).one_or_none()
    elif type(token_type) is TokenTypes:
        type_found = TokenTypes.query.filter_by(type=token_type.type).one_or_none()
    else:
        type_found = None
    if not type_found:
        return
    token = create_access_token(identity=user.id,
                                user_claims={'type': token_type.type}, # type --> livello del token, a cosa puo accedere
                                expires_delta=expiration) # quanto tempo dura prima che scada
    add_token_to_database(token, user)
    return token


def add_token_to_database(encoded_token, user):
    """
    Adds a new token to the database. It is not revoked when it is added.
    :param identity_claim:
    """
    decoded_token = decode_token(encoded_token)
    jti = decoded_token['jti']
    token_type = TokenTypes.query.filter_by(type=decoded_token['user_claims']['type']).one()
    if 'exp' in decoded_token:
        expires = _epoch_utc_to_datetime(decoded_token['exp'])
    else:
        expires = None
    revoked = False

    db_token = Tokens(
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
    bearer_token = request.headers.get('Authorization','Bearer ')
    token = bearer_token.partition('Bearer ')[2]
    #jti = decoded_token['jti']
    try:
        token = Tokens.query.filter_by(token=token).one()
        return token.revoked
    except NoResultFound:
        return True


def get_user_tokens(user):
    """
    Returns all of the tokens, revoked and unrevoked, that are stored for the
    given user
    """
    return Tokens.query.filter_by(user=user).all()


def revoke_token(token_id, user):
    """
    Revokes the given token. Raises a TokenNotFound error if the token does
    not exist in the database
    """
    try:
        token = Tokens.query.filter_by(id=token_id, user=user).one()
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
        token = Tokens.query.filter_by(id=token_id, user=user).one()
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
    expired = Tokens.query.filter(Tokens.expires < now).all()
    for token in expired:
        db.session.delete(token)
    db.session.commit()

class TokenNotFound(Exception):
    """
    Indicates that a token could not be found in the database
    """
    pass
