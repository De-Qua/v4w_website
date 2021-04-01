import pdb
from urllib.parse import urlparse, quote
from functools import wraps

## FLASK IMPORTS
from flask import request, current_app
from flask_restful import Resource, reqparse
from flask_jwt_extended import (
        get_raw_jwt, verify_jwt_in_request, get_jwt_claims
)

# INTERNAL IMPORTS
from app import db
from app.src.libpy.lib_search import find_address_in_db, check_if_is_already_a_coordinate
from app.src.libpy.lib_graph import estimate_path_length_time
from app.src.interface import find_what_needs_to_be_found
from app.models import Tokens, TokenApiCounters, Apis, TokenTypes, Languages, ErrorCodes, ErrorTranslations
from app import custom_errors
from app.src.libpy import lib_graph_tool as lgt
from app.src.libpy import lib_weights as lw
from app.src.interface_API import get_current_tide_level
import traceback

# ERROR_CODES
from app.src.api.constants import *


def api_response(code=0, data={}, message= '', lang=DEFAULT_LANGUAGE_CODE):
    response = {
        'ResponseCode': code,
        'ResponseMessage': message,
        'ResponseData': data
    }
    if code == 0:
        response['ResponseMessage'] = 'OK'
        return response
    else:
        default_language = Languages.query.filter_by(code=DEFAULT_LANGUAGE_CODE).one()
        default_error = ErrorCodes.query.filter_by(code=GENERIC_ERROR_CODE).one()
        language = Languages.query.filter((Languages.code == lang.lower()) | (Languages.name == lang.lower())).one_or_none()
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


def verify_permissions(type, url, lang=DEFAULT_LANGUAGE_CODE):
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
            return api_response(code=NO_PERMISSION)
    return wrapper


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


class getAddress(Resource):
    """
    API to retrieve coordinates from an address
    """

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('address', type=str, required=True,
                                   help="No address provided")
        self.reqparse.add_argument('language', type=str, default=DEFAULT_LANGUAGE_CODE)
        super(getAddress, self).__init__()

    @permission_required
    def get(self):
        update_api_counter()
        try:
            args = self.reqparse.parse_args()
        except Exception as e:
            err_msg = e.data['message']
            all_err = [err_msg[argument] for argument in err_msg.keys()]
            msg = '. '.join(all_err)
            return api_response(code=UNKNOWN_EXCEPTION, message=msg)
        address = args['address']
        lang = args['language']
        try:
            result_dict = find_address_in_db(address)
        except Exception:
            return api_response(code=RETURNED_EXCEPTION, lang=lang)
        if len(result_dict) > 1:
            return api_response(code=UNCLEAR_SEARCH, lang=lang)
        data = {'address': result_dict[0]['nome'],
                'longitude': result_dict[0]['coordinate'][0],
                'latitude': result_dict[0]['coordinate'][1]
                }
        return api_response(data=data)


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
        self.reqparse.add_argument('language', type=str, default=DEFAULT_LANGUAGE_CODE)
        super(getPath, self).__init__()

    @permission_required
    def get(self):
        update_api_counter()
        try:
            args = self.reqparse.parse_args()
        except Exception as e:
            err_msg = e.data['message']
            all_err = [err_msg[argument] for argument in err_msg.keys()]
            msg = '. '.join(all_err)
            return api_response(code=UNKNOWN_EXCEPTION, message=msg)
        lang = args['language']
        is_coordinate_start, coords_start = check_if_is_already_a_coordinate(args['start'])
        is_coordinate_end, coords_end = check_if_is_already_a_coordinate(args['end'])
        if not is_coordinate_start or not is_coordinate_end:
            api_response(code=MISSING_PARAMETER, lang=lang)
        default_params = set_default_request_variables()
        user_params = {
            'da': args['start'],
            'a': args['end'],
            'start_coord': args['start'],
            'end_coord': args['end']
        }
        params_research = dict(default_params, **user_params)
        try:
            path = find_what_needs_to_be_found(params_research)
        except custom_errors.UserError:
            url_args = args
            url_args.pop('start')
            dequa_url = create_url_from_inputs(args)
            data = {
                'length': -1,
                'time': -1,
                'url': dequa_url
            }
            return api_response(code=NOT_FOUND, data=data, lang=lang)
        except Exception as e:
            return api_response(code=NOT_FOUND, lang=lang)
        dequa_url = create_url_from_inputs(args)
        data = {
            'length': path['path']['lunghezza'],
            'time': path['path']['time'],
            'url': dequa_url
        }
        return api_response(data=data)


class getMultiplePaths(Resource):
    """
    Api to retrieve, given a multiple starting points and one ending point,
    the estimated time and the length of the shortest paths from each starting
    point to the ending point.
    """

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('start', type=str, required=True,
                                   help="No starting point provided",
                                   action='append')
        self.reqparse.add_argument('end', required=True,
                                   help="No ending point provided")
        self.reqparse.add_argument('speed', type=float, default=5)
        self.reqparse.add_argument('mode', type=str, choices=('walk'), default="walk",
                                    help="Mode {mode} not supported")
        self.reqparse.add_argument('language', type=str, default=DEFAULT_LANGUAGE_CODE)
        super(getMultiplePaths, self).__init__()

    @permission_required
    def get(self):
        update_api_counter()
        try:
            args = self.reqparse.parse_args()
        except Exception as e:
            err_msg = e.data['message']
            all_err = [err_msg[argument] for argument in err_msg.keys()]
            msg = '. '.join(all_err)
            return api_response(code=UNKNOWN_EXCEPTION, message=msg)
        lang = args['language']
        is_coord, end_coords = check_if_is_already_a_coordinate(args['end'])
        if not is_coord:
            return api_response(code=MISSING_PARAMETER, lang=lang)
        # default_params = set_default_request_variables()
        all_length_time = {}
        for start_point in args['start']:
            is_coord, start_coords = check_if_is_already_a_coordinate(start_point)
            if not is_coord:
                return api_response(code=MISSING_PARAMETER, lang=lang)
            all_length_time[start_point] = estimate_path_length_time(start_coords, end_coords,
                    speed=args['speed'])

        return api_response(data=all_length_time)


class getPathStreetInfo(Resource):
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
        self.reqparse.add_argument('stop', type=str, required=False,
                                   action="append")
        self.reqparse.add_argument('speed', type=float, default=5)
        self.reqparse.add_argument('mode', type=str, default="foot")
        self.reqparse.add_argument('tide', type=int, default=None)
        self.reqparse.add_argument('waterbus', type=bool, default=False)
        self.reqparse.add_argument('language', type=str, default=DEFAULT_LANGUAGE_CODE)
        super(getPathStreetInfo, self).__init__()

    @permission_required
    def get(self):
        update_api_counter()
        try:
            args = self.reqparse.parse_args()
        except Exception as e:
            err_msg = e.data['message']
            all_err = [err_msg[argument] for argument in err_msg.keys()]
            msg = '. '.join(all_err)
            return api_response(code=UNKNOWN_EXCEPTION, message=msg)
        lang = args['language']
        # validate the coordinates
        is_coord, start_coords = check_if_is_already_a_coordinate(args['start'])
        if not is_coord:
            return api_response(code=MISSING_PARAMETER, lang=lang)
        is_coord, end_coords = check_if_is_already_a_coordinate(args['end'])
        if not is_coord:
            return api_response(code=MISSING_PARAMETER, lang=lang)
        if args['stop']:
            are_coords, stop_coords = [check_if_is_already_a_coordinate(c) for c in args['stop']]
            if not all(are_coords):
                return api_response(code=MISSING_PARAMETER, lang=lang)
        else:
            stop_coords = None
        # Define the weight that we will use
        if args['mode'] == 'bridge':
            weight = lw.get_weight_bridges(
                        graph=current_app.graphs['street']['graph'],
                        speed=args['speed'])
        elif args['mode'] == 'tide':
            if not args['tide']:
                args['tide'] = get_current_tide_level()
            weight = lw.get_weight_tide(
                        graph=current_app.graphs['street']['graph'],
                        tide_level=args['tide'],
                        speed=args['speed'])
        else:  # default is foot
            weight = lw.get_weight_time(
                        graph=current_app.graphs['street']['graph'],
                        speed=5)
        # check the format, maybe we can change it with just a try/except
        try:
            v_list, e_list = lgt.calculate_path(
                        graph=current_app.graphs['street']['graph'],
                        coords_start=[start_coords],
                        coords_end=[end_coords],
                        coords_stop=stop_coords,
                        weight=weight,
                        all_vertices=current_app.graphs['street']['all_vertices']
                        )
            info = lgt.retrieve_info_from_path_streets(
                        graph=current_app.graphs['street']['graph'],
                        paths_vertices=v_list,
                        paths_edges=e_list
                        )
            return api_response(data=info)
        except Exception:
            traceback.print_exc()
            return api_response(code=NOT_FOUND, lang=lang)


class getCurrentTide(Resource):
    """
    Api to retrieve the time and the length of the shortest path
    between two coordinates
    """

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('language', type=str, default=DEFAULT_LANGUAGE_CODE)
        super(getCurrentTide, self).__init__()

    @permission_required
    def get(self):
        update_api_counter()
        try:
            args = self.reqparse.parse_args()
        except Exception as e:
            err_msg = e.data['message']
            all_err = [err_msg[argument] for argument in err_msg.keys()]
            msg = '. '.join(all_err)
            return api_response(code=UNKNOWN_EXCEPTION, message=msg)
        lang = args['language']
        # validate the coordinates
        try:
            tide = get_current_tide_level()
            return api_response(data={'tide': tide})
        except Exception:
            return api_response(code=NOT_FOUND, lang=lang)
