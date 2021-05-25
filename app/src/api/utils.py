import pdb
from urllib.parse import urlparse, quote
from functools import wraps

from flask import request

# Token
from flask_jwt_extended import (
        get_raw_jwt, verify_jwt_in_request, get_jwt_claims
)

# Database
from app.models import (
        Tokens, TokenApiCounters, Apis, TokenTypes,
        Languages, ErrorCodes, ErrorTranslations
)
from app import app, db

# ERROR_CODES
from app.src.api import constants as cst
# from app.src.api.constants import (
#     DEFAULT_LANGUAGE_CODE,
#     GENERIC_ERROR_CODE, NO_PERMISSION
# )


def api_response(code=0, data={}, message='', lang=cst.DEFAULT_LANGUAGE_CODE):
    """
    Format the response of the api in a standardize way
    """
    response = {
        'ResponseCode': code,
        'ResponseMessage': message,
        'ResponseData': data
    }
    if code == 0:
        response['ResponseMessage'] = 'OK'
        return response
    else:
        default_language = Languages.query.filter_by(code=cst.DEFAULT_LANGUAGE_CODE).one()
        default_error = ErrorCodes.query.filter_by(code=cst.GENERIC_ERROR_CODE).one()
        language = Languages.query.filter(
            (Languages.code == lang.lower()) | (Languages.name == lang.lower())
            ).one_or_none()
        if not language:
            language = default_language
        error = ErrorCodes.query.filter_by(code=code).one_or_none()
        if not error:
            error = default_error
        err_message = ErrorTranslations.query.join(ErrorCodes).filter_by(
            code=error.code).join(Languages).filter_by(code=language.code).one_or_none()
        if not err_message:
            err_message = ErrorTranslations.query.join(ErrorCodes).filter_by(
                code=error.code).join(Languages).filter_by(code=default_language.code).one_or_none()

        response['ResponseMessage'] = err_message.message
        if message:
            response['ResponseMessage'] += f" - {message}"
        response['ResponseData'] = data
        return response


# Decorators
def permission_required(fn):
    """ Here is a custom decorator that verifies the JWT is present in
    the request, as well as insuring that this user has the permission
    to access the api
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        claims = get_jwt_claims()
        api_path = request.base_url
        if (verify_permissions(claims['type'], api_path)
                or '127.0.0.1:5000' in api_path
                or 'dequa.it' in api_path):
            return fn(*args, **kwargs)
        else:
            return api_response(code=cst.NO_PERMISSION)
        return fn(*args, **kwargs)
    return wrapper


def update_api_counter(fn):
    """
    Decorator to automatically update the current api with the current token
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        api_path = request.base_url
        token = extract_current_token()
        update_api_token_counter(token, api_path)
        return fn(*args, **kwargs)
    return wrapper


# API arguments
def parse_args(reqparse):
    """Function to parse the arguments of an api.

    :param reqparse: reqparse object.
    :return: dictionary with the arguments.

    """
    try:
        args = reqparse.parse_args()
        return args
    except Exception as e:
        err_msg = e.data['message']
        all_err = [err_msg[argument] for argument in err_msg.keys()]
        msg = '. '.join(all_err)
        return api_response(code=cst.BAD_FORMAT_REQUEST, message=msg)

# Token

def extract_current_token():
    """
    In a protected endpoint extracts the Token entry
    """
    jti = get_raw_jwt()['jti']
    token = Tokens.query.filter_by(jti=jti).one_or_none()
    return token


def extract_api_from_url(url):
    """
    Helper function that extract the Api entry from a dequa url path
    """
    if urlparse(url).scheme:
        api_address = url.split('/api/')[1]
    else:
        api_address = url
    api = Apis.query.filter_by(path=api_address).one_or_none()
    return api


def update_api_token_counter(token, url):
    """
    Function to update the api counter from one specific token
    """
    # if it is a Token from the database use it, otherwise we assume it is a jti
    if not type(token) == Tokens:
        token = Tokens.query.filter_by('jti').one_or_none()

    api = extract_api_from_url(url)

    if not token or not api:
        app.logger.warning("No token or No api")
        return None

    counter = TokenApiCounters.query.filter_by(token=token, api=api).one_or_none()
    if not counter:
        counter = TokenApiCounters(token=token, api=api, count=0)
    counter.count += 1
    db.session.add(counter)
    db.session.commit()


def verify_permissions(type, url, lang=cst.DEFAULT_LANGUAGE_CODE):
    """
    Helper function that verifies if a token type has permission for an url
    """
    token_type = TokenTypes.query.filter_by(type=type).one_or_none()
    if not token_type:
        return False

    api = extract_api_from_url(url)
    if api not in token_type.permissions:
        return False

    else:
        return True


# FUNCTIONS FOR OLD API


def create_url_from_inputs(args):
    start_point = args.get('start', '')
    end_point = args.get('end', '')
    mode = args.get('mode','')
    base_url = 'https://www.dequa.it'
    start_key = 'partenza'
    end_key = 'arrivo'
    if mode == 'walk':
        mode_key = 'walk'
    elif mode == 'boat':
        mode_key = 'boat'
    else:
        mode_key = 'walk'
    final_url = base_url + '/?' + \
                start_key + '=' + quote(start_point) + \
                '&' + end_key + '=' + quote(end_point) + \
                '&' + mode_key + '=' + 'on'
    return final_url


def set_default_request_variables():
    """
    Helper function to set the request variables as request by dequa
    """
    params = {
        'less_bridges': 'off',
        'with_tide': 'off',
        'by_boat': 'off',
        'tide_level': None
    }
    return params
