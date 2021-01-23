import pdb
from urllib.parse import urlparse
from functools import wraps

from flask import request
from flask_restful import Resource, reqparse, abort
from flask_jwt_extended import (
        jwt_required, get_raw_jwt, verify_jwt_in_request, get_jwt_claims
)

from app import db
from app.src.libpy.lib_search import find_address_in_db
from app.src.interface import find_what_needs_to_be_found

from app.models import Tokens, TokenApiCounters, Apis, TokenTypes


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
        return None

    counter = TokenApiCounters.query.filter_by(token=token, api=api).one_or_none()
    if not counter:
        counter = TokenApiCounters(token=token, api=api, count=0)
    counter.count += 1
    db.session.add(counter)
    db.session.commit()


def update_api_counter():
    """
    Function to automatically update the current api with the current token
    """
    api_path = request.base_url
    token = extract_current_token()
    return update_api_token_counter(token, api_path)


def verify_permissions(type, url):
    """
    Helper function that verifies if a token type has permission for an url
    """
    token_type = TokenTypes.query.filter_by(type=type).one_or_none()
    if not token_type:
        return abort(403,
                     error="Not supported token type",
                     message="Il tipo di token non è stato trovato nel databse"
                     )
    api = extract_api_from_url(url)
    if api not in token_type.permissions:
        return abort(403,
                     error="Access denied",
                     message="Non hai il permesso per accedere a questa api"
                     )
    else:
        return True


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
        if verify_permissions(claims['type'], api_path):
            return fn(*args, **kwargs)
        else:
            return abort(403,
                         error="Access denied",
                         message="Non hai il permesso per accedere a questa api"
                         )
    return wrapper


class GetAddressAPI(Resource):
    """
    API to retrieve coordinates from an address
    """

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('address', type=str, required=True,
                                   help="No address provided")
        super(GetAddressAPI, self).__init__()

    @permission_required
    def get(self):
        update_api_counter()
        args = self.reqparse.parse_args()
        address = args['address']
        try:
            result_dict = find_address_in_db(address)
        except:
            abort(404,
                  error="Address not in the database",
                  message=f"L'indirizzo {address} non è stato trovato nel database")

        return {'coord': result_dict[0]['coordinate']}, 201


class getPath(Resource):
    """
    Api to retrieve the time and the length of the shortest path
    between two coordinates
    """

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('start', type=str, required=True,
                                   help="No starting point provided")
        self.reqparse.add_argument('end', type=str, required=True,
                                   help="No ending point provided")
        self.reqparse.add_argument('speed', type=float, default=5)
        self.reqparse.add_argument('mode', type=str, default="foot")
        super(getPath, self).__init__()

    @permission_required
    def get(self):
        update_api_counter()
        args = self.reqparse.parse_args()
        default_params = set_default_request_variables()
        user_params = {
            'da': args['start'],
            'a': args['end'],
            'start_coord': args['start'],
            'end_coord': args['end']
        }
        params_research = dict(default_params, **user_params)
        path = find_what_needs_to_be_found(params_research)
        length_time = {
            'length': path['path']['lunghezza'],
            'time': path['path']['time']
        }
        return length_time


class getPathsMultiEnd(Resource):
    """
    Api to retrieve, given a start point and multiple end point,
    the time and the length of the shortest paths
    """

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('start', type=str, required=True,
                                   help="No starting point provided")
        self.reqparse.add_argument('end', required=True,
                                   help="No ending point provided",
                                   action='append')
        self.reqparse.add_argument('speed', type=float, default=5)
        self.reqparse.add_argument('mode', type=str, default="foot")
        super(getPathsMultiEnd, self).__init__()

    @permission_required
    def get(self):
        update_api_counter()
        args = self.reqparse.parse_args()
        default_params = set_default_request_variables()
        all_length_time = {}
        for end_point in args['end']:
            user_params = {
                'da': args['start'],
                'a': end_point,
                'start_coord': args['start'],
                'end_coord': end_point
            }
            params_research = dict(default_params, **user_params)
            path = find_what_needs_to_be_found(params_research)
            length_time = {
                'length': path['path']['lunghezza'],
                'time': path['path']['time']
            }
            all_length_time[end_point] = length_time
        return all_length_time
