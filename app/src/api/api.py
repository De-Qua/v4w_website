import ipdb
import json

# FLASK IMPORTS
from flask_restful import Resource, reqparse, inputs
from flask import current_app, request


# INTERNAL IMPORTS
from app.src.libpy.lib_search import find_address_in_db, check_if_is_already_a_coordinate
from app.src.libpy.lib_graph import estimate_path_length_time
from app.src.interface import find_what_needs_to_be_found

from app import custom_errors
from dequa_graph.topology import calculate_path
from dequa_graph.formatting import retrieve_info_from_path_streets
from dequa_graph import weights as dqg_w
from app.src.interface_API import get_current_tide_level, get_suggestions, get_places
import traceback

# ERROR_CODES
from app.src.api.constants import (
    DEFAULT_LANGUAGE_CODE,
    UNKNOWN_EXCEPTION, MISSING_PARAMETER, NOT_FOUND, RETURNED_EXCEPTION,
    UNCLEAR_SEARCH, GENERIC_ERROR_CODE, BAD_FORMAT_REQUEST
)
from app.src.api import errors as err
# UTILS
from app.src.api.utils import (
    api_response,
    permission_required, update_api_counter
)
# Utils for networkx graph
from app.src.api.utils import create_url_from_inputs, set_default_request_variables
# Interface for the api
from app.src import interface_API as iAPI
from app.src.interface_API import check_format_coordinates


AVAILABLE_APIS = {
    "getPlaces": {
        "name": "ricerca",
        "endpoint": "search"
    },
    "getSuggestions": {
        "name": "suggerimenti",
        "endpoint": "suggest"
    },
    "getGeneralPath": {
        "name": "general path",
        "endpoint": "path"
    },
    "getPathStreet": {
        "name": "path street",
        "endpoint": "gt_path"
    },
    "getPathWater": {
        "name": "path water",
        "endpoint": "gt_path_water"
    },
    "getAddress": {
        "name": "old address",
        "endpoint": "address"
    },
    "getSystemInfo": {
        "name": "system info",
        "endpoint": "system_info"
    },
    "generateShortUrl": {
        "name": "generate url",
        "endpoint": "generate_url"
    },
    "resolveShortUrl": {
        "name": "resolve url",
        "endpoint": "resolve_url"
    }
}


#  ██████  ███████ ███    ██ ███████ ██████   █████  ██
# ██       ██      ████   ██ ██      ██   ██ ██   ██ ██
# ██   ███ █████   ██ ██  ██ █████   ██████  ███████ ██
# ██    ██ ██      ██  ██ ██ ██      ██   ██ ██   ██ ██
#  ██████  ███████ ██   ████ ███████ ██   ██ ██   ██ ███████

# ██████   █████  ████████ ██   ██
# ██   ██ ██   ██    ██    ██   ██
# ██████  ███████    ██    ███████
# ██      ██   ██    ██    ██   ██
# ██      ██   ██    ██    ██   ██


class getGeneralPath(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('start', type=str, required=True,
                                   help="No starting point provided")
        self.reqparse.add_argument('end', type=str, required=True,
                                   help="No ending point provided")
        self.reqparse.add_argument('stop', type=str, required=False,
                                   action="append", default=None)
        self.reqparse.add_argument('options', type=dict, required=True,
                                   help="No options provided")
        self.optparse = reqparse.RequestParser()
        self.optparse.add_argument('method', type=str, required=False, choices=("walk", "boat"), default="walk", location=('options',))
        self.optparse.add_argument('time', type=inputs.datetime_from_iso8601, required=False, default=None, location=('options',))
        self.optparse.add_argument('tideLevel', type=int, required=False, default=0, location=('options',))
        self.optparse.add_argument('language', type=str, default=DEFAULT_LANGUAGE_CODE, location=('options',))
        self.optparse.add_argument('alternatives', type=inputs.boolean, default=False, location=('options',))
        self.optparse.add_argument('walkingOptions', type=dict, required=False, location=('options',))
        self.optparse.add_argument('boatOptions', type=dict, required=False, location=('options',))
        self.optparse.add_argument('accessibleOptions', type=dict, required=False, location=('options',))

        self.walkparse = reqparse.RequestParser()
        self.walkparse.add_argument("walkSpeed", type=float, default=5/3.6, location=('walkingOptions',))
        self.walkparse.add_argument("avoidTide", type=inputs.boolean, default=False, location=('walkingOptions',))
        self.walkparse.add_argument("avoidPublicTransport", type=inputs.boolean, default=True, location=('walkingOptions',))
        self.walkparse.add_argument("bridgeWeight", type=int, default=1, location=('walkingOptions',))
        self.walkparse.add_argument("bootsHeight", type=int, default=30, location=('walkingOptions',))
        self.walkparse.add_argument("preferPublicTransport", type=inputs.boolean, default=False, location=('walkingOptions',))
        self.walkparse.add_argument("useAccessibleOptions", type=inputs.boolean, default=False, location=('walkingOptions', ))

        self.boatparse = reqparse.RequestParser()
        self.boatparse.add_argument("walkSpeed", type=float, default=5, location=("boatOptions",))
        self.boatparse.add_argument("avoidTide", type=inputs.boolean, default=False, location=("boatOptions",))
        self.boatparse.add_argument("avoidPublicTransport", type=inputs.boolean, default=True, location=("boatOptions",))
        self.boatparse.add_argument("preferPublicTransport", type=inputs.boolean, default=False, location=('boatOptions',))
        self.boatparse.add_argument("bridgeWeight", type=int, default=1, location=("boatOptions",))
        self.boatparse.add_argument("bootsHeight", type=int, default=30, location=("boatOptions",))
        self.boatparse.add_argument("boatSpeed", type=float, default=5/3.6, location=("boatOptions",))
        self.boatparse.add_argument("width", type=float, default=1.5, location=("boatOptions",))
        self.boatparse.add_argument("height", type=float, default=1, location=("boatOptions",))
        self.boatparse.add_argument("draft", type=float, default=0.3, location=("boatOptions",))
        self.boatparse.add_argument("type", type=str, choices=("motor", "row", "generic"), default="motor", location=("boatOptions",))

        self.accessparse = reqparse.RequestParser()
        self.accessparse.add_argument("walkSpeed", type=float, default=5/3.6, location=("accessibleOptions",))
        self.accessparse.add_argument("avoidTide", type=inputs.boolean, default=False, location=("accessibleOptions",))
        self.accessparse.add_argument("avoidPublicTransport", type=inputs.boolean, default=False, location=("accessibleOptions",))
        self.accessparse.add_argument("preferPublicTransport", type=inputs.boolean, default=True, location=('boatOptions',))
        self.accessparse.add_argument("bridgeWeight", type=int, default=1, location=("accessibleOptions",))
        self.accessparse.add_argument("bootsHeight", type=int, default=30, location=("accessibleOptions",))
        self.accessparse.add_argument("width", type=float, default=0.7, location=("accessibleOptions",))

        super(getGeneralPath, self).__init__()

    @permission_required
    @update_api_counter
    def post(self):
        try:
            args = self.reqparse.parse_args()
            opt = self.optparse.parse_args(req=args)
            boat = self.boatparse.parse_args(req=opt)
            if opt["method"] == "walk":
                mode = "walk"
                walk = self.walkparse.parse_args(req=opt)
                if walk["useAccessibleOptions"]:
                    walk = self.accessparse.parse_args(req=opt)

            # elif opt["method"] == "accessible":
            #     mode = "walk"
            #     walk = self.accessparse.parse_args(req=opt)
            elif opt["method"] == "boat":
                mode = "boat"
                walk = boat
        except Exception as e:
            err_msg = e.data['message']
            all_err = [err_msg[argument] for argument in err_msg.keys()]
            msg = '. '.join(all_err)
            return api_response(code=BAD_FORMAT_REQUEST, message=msg)

        avoid_bridges = walk["bridgeWeight"] > 1

        # args = request.get_json()
        lang = opt['language']
        # alternatives = False
        try:
            start_coords, end_coords = check_format_coordinates(args['start'], args['end'])
            if args['stop']:
                stop_coords = check_format_coordinates(args['stop'])
            else:
                stop_coords = None
        except (err.CoordinatesFormatError, err.CoordinatesNumberError) as e:
            return api_response(code=e.code, lang=lang)
        # call the interface to handle everythin

        try:
            info = iAPI.find_shortest_path_from_coordinates(
                mode=mode,
                start=start_coords, end=end_coords, stop=stop_coords,
                speed=walk["walkSpeed"], avoid_bridges=avoid_bridges,
                avoid_tide=walk["avoidTide"], tide_level=opt['tideLevel'],
                boots_height=walk['bootsHeight'],
                avoid_public_transport=walk["avoidPublicTransport"],
                prefer_public_transport=walk["preferPublicTransport"],
                start_time=opt["time"],
                motor=boat["type"] == "motor", boat_speed=boat["boatSpeed"],
                boat_width=boat["width"], boat_height=boat["height"], boat_draft=boat["draft"],
                alternatives=opt["alternatives"]
            )
            return api_response(data=info, lang=lang)
        except Exception as e:
            current_app.logger.error(str(e))
            return api_response(code=getattr(e, 'code', GENERIC_ERROR_CODE), lang=lang)


class getPathStreet(Resource):
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
                                   action="append", default=None)
        self.reqparse.add_argument('speed', type=float, default=5)
        # self.reqparse.add_argument('mode', type=str,
        #                            choices=["walk", "bridge", "tide"],
        #                            default="walk")
        self.reqparse.add_argument('avoid_bridges', type=inputs.boolean, default=False)
        self.reqparse.add_argument('avoid_tide', type=inputs.boolean, default=False)
        self.reqparse.add_argument('tide', type=int, default=None)
        self.reqparse.add_argument('waterbus', type=inputs.boolean, default=False)
        self.reqparse.add_argument('alternatives', type=inputs.boolean, default=False)
        self.reqparse.add_argument('language', type=str, default=DEFAULT_LANGUAGE_CODE)
        super(getPathStreet, self).__init__()

    @permission_required
    @update_api_counter
    def get(self):
        try:
            args = self.reqparse.parse_args()
        except Exception as e:
            err_msg = e.data['message']
            all_err = [err_msg[argument] for argument in err_msg.keys()]
            msg = '. '.join(all_err)
            return api_response(code=BAD_FORMAT_REQUEST, message=msg)
        lang = args['language']
        # validate the coordinates
        try:
            start_coords, end_coords = check_format_coordinates(args['start'], args['end'])
            if args['stop']:
                stop_coords = check_format_coordinates(args['stop'])
            else:
                stop_coords = None
        except (err.CoordinatesFormatError, err.CoordinatesNumberError) as e:
            return api_response(code=e.code, lang=lang)
        # call the interface to handle everythin
        try:
            info = iAPI.find_shortest_path_from_coordinates(
                start=start_coords, end=end_coords, stop=stop_coords,
                speed=args['speed'], avoid_bridges=args['avoid_bridges'],
                avoid_tide=args['avoid_tide'], tide=args['tide'],
                waterbus=args['waterbus'], alternatives=args['alternatives']
            )
            return api_response(data=info, lang=lang)
        except Exception as e:
            current_app.logger.error(str(e))
            return api_response(code=getattr(e, 'code', GENERIC_ERROR_CODE), lang=lang)


class getPathWater(Resource):
    """
    Api to retrieve the time and the length of the shortest water path
    between two coordinates
    """

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('start', type=str, required=True,
                                   help="No starting point provided")
        self.reqparse.add_argument('end', type=str, required=True,
                                   help="No ending point provided")
        self.reqparse.add_argument('stop', type=str, required=False,
                                   action="append", default=None)
        self.reqparse.add_argument('speed', type=float, default=5)
        # self.reqparse.add_argument('mode', type=str,
        #                            choices=["walk", "bridge", "tide"],
        #                            default="walk")
        self.reqparse.add_argument('motor', type=inputs.boolean, default=False)
        self.reqparse.add_argument('width', type=float, default=0)
        self.reqparse.add_argument('height', type=float, default=0)
        self.reqparse.add_argument('alternatives', type=inputs.boolean, default=False)
        self.reqparse.add_argument('language', type=str, default=DEFAULT_LANGUAGE_CODE)
        super(getPathWater, self).__init__()

    @permission_required
    @update_api_counter
    def get(self):
        try:
            args = self.reqparse.parse_args()
        except Exception as e:
            err_msg = e.data['message']
            all_err = [err_msg[argument] for argument in err_msg.keys()]
            msg = '. '.join(all_err)
            return api_response(code=BAD_FORMAT_REQUEST, message=msg)
        # ipdb.set_trace()
        lang = args['language']
        # validate the coordinates
        try:
            start_coords, end_coords = check_format_coordinates(args['start'], args['end'])
            if args['stop']:
                stop_coords = check_format_coordinates(args['stop'])
            else:
                stop_coords = None
        except (err.CoordinatesFormatError, err.CoordinatesNumberError) as e:
            return api_response(code=e.code, lang=lang)
        # call the interface to handle everythin
        try:
            info = iAPI.find_shortest_path_from_coordinates(
                mode="boat",
                start=start_coords, end=end_coords, stop=stop_coords,
                motor=args['motor'], boat_speed=args['speed'],
                boat_width=args['width'], boat_height=args['height'],
                alternatives=args['alternatives']
            )
            return api_response(data=info, lang=lang)
        except Exception as e:
            current_app.logger.error(str(e))
            return api_response(code=getattr(e, 'code', GENERIC_ERROR_CODE), lang=lang)


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
    @update_api_counter
    def get(self):
        try:
            args = self.reqparse.parse_args()
        except Exception as e:
            err_msg = e.data['message']
            all_err = [err_msg[argument] for argument in err_msg.keys()]
            msg = '. '.join(all_err)
            return api_response(code=BAD_FORMAT_REQUEST, message=msg)
        lang = args['language']
        # validate the coordinates
        try:
            tide = get_current_tide_level()
            return api_response(data={'tide': tide})
        except Exception:
            return api_response(code=NOT_FOUND, lang=lang)


# ███████ ██    ██  ██████   ██████  ███████ ███████ ████████ ██  ██████  ███    ██ ███████
# ██      ██    ██ ██       ██       ██      ██         ██    ██ ██    ██ ████   ██ ██
# ███████ ██    ██ ██   ███ ██   ███ █████   ███████    ██    ██ ██    ██ ██ ██  ██ ███████
#      ██ ██    ██ ██    ██ ██    ██ ██           ██    ██    ██ ██    ██ ██  ██ ██      ██
# ███████  ██████   ██████   ██████  ███████ ███████    ██    ██  ██████  ██   ████ ███████


class getSuggestions(Resource):
    """
    API to retrieve names from the database
    """

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('name', type=str, required=True,
                                   help="No name provided")
        self.reqparse.add_argument('max_num', type=int, default=5)
        self.reqparse.add_argument('language', type=str, default=DEFAULT_LANGUAGE_CODE)
        super(getSuggestions, self).__init__()

    @permission_required
    def get(self):
        try:
            args = self.reqparse.parse_args()
        except Exception as e:
            err_msg = e.data['message']
            all_err = [err_msg[argument] for argument in err_msg.keys()]
            msg = '. '.join(all_err)
            return api_response(code=UNKNOWN_EXCEPTION, message=msg)
        name = args['name']
        max_num = args['max_num']
        lang = args['language']
        try:
            suggestions = get_suggestions(name, max_num)
        except Exception:
            return api_response(code=RETURNED_EXCEPTION, lang=lang)

        return api_response(data=suggestions)


class getPlaces(Resource):
    """
    API to retrieve address, streets or pois from the database
    """

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('name', type=str, required=True,
                                   help="No name provided")
        self.reqparse.add_argument('max_num', type=int, default=10)
        self.reqparse.add_argument('language', type=str, default=DEFAULT_LANGUAGE_CODE)
        super(getPlaces, self).__init__()

    @permission_required
    @update_api_counter
    def get(self):
        try:
            args = self.reqparse.parse_args()
        except Exception as e:
            err_msg = e.data['message']
            all_err = [err_msg[argument] for argument in err_msg.keys()]
            msg = '. '.join(all_err)
            return api_response(code=UNKNOWN_EXCEPTION, message=msg)
        name = args['name']
        max_num = args['max_num']
        lang = args['language']
        try:
            places = get_places(name, max_num=max_num)
        except Exception:
            return api_response(code=RETURNED_EXCEPTION, lang=lang)

        return api_response(data=places)


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
    @update_api_counter
    def get(self):
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
            data = []
            for r in result_dict:
                data_candidate = {}
                for _key in r.keys():
                    data_candidate[_key] = r[_key]
                data.append(data_candidate)
            return api_response(code=UNCLEAR_SEARCH, lang=lang, data=data)
        data = []
        # {'address': result_dict[0]['nome'],
        #         'longitude': result_dict[0]['coordinate'][0],
        #         'latitude': result_dict[0]['coordinate'][1],
        #         'info': result_dict[0]['info']
        #         }
        data_candidate = {}
        for _key in r.keys():
            data_candidate[_key] = r[_key]
        data.append(data_candidate)
        return api_response(data=data)


# ███████ ██    ██ ███████ ████████ ███████ ███    ███     ██ ███    ██ ███████  ██████
# ██       ██  ██  ██         ██    ██      ████  ████     ██ ████   ██ ██      ██    ██
# ███████   ████   ███████    ██    █████   ██ ████ ██     ██ ██ ██  ██ █████   ██    ██
#      ██    ██         ██    ██    ██      ██  ██  ██     ██ ██  ██ ██ ██      ██    ██
# ███████    ██    ███████    ██    ███████ ██      ██     ██ ██   ████ ██       ██████


class getSystemInfo(Resource):
    """
    API to retrieve info about the system
    """

    def __init__(self):
        super(getSystemInfo, self).__init__()

    @permission_required
    @update_api_counter
    def get(self):
        info = current_app.info
        variables = current_app.current_variables
        tide_values = current_app.tide_values
        data = {
            "info": info,
            "variables": variables,
            "tide": tide_values
            }
        return api_response(data=data)


# ███████ ██   ██  ██████  ██████  ████████     ██    ██ ██████  ██
# ██      ██   ██ ██    ██ ██   ██    ██        ██    ██ ██   ██ ██
# ███████ ███████ ██    ██ ██████     ██        ██    ██ ██████  ██
#      ██ ██   ██ ██    ██ ██   ██    ██        ██    ██ ██   ██ ██
# ███████ ██   ██  ██████  ██   ██    ██         ██████  ██   ██ ███████

class generateShortUrl(Resource):
    """
    API to generate a unique short url
    """

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('payload', type=dict, required=True,
                                   help="No payload provided")
        self.reqparse.add_argument('endpoint', type=str, required=True,
                                   help="No endpoint provided")
        self.reqparse.add_argument('words', type=str, required=False,
                                   help="use to choose words generator instead of short code")
        super(generateShortUrl, self).__init__()

    def post(self):
        try:
            args = self.reqparse.parse_args()
        except Exception as e:
            err_msg = e.data['message']
            all_err = [err_msg[argument] for argument in err_msg.keys()]
            msg = '. '.join(all_err)
            return api_response(code=UNKNOWN_EXCEPTION, message=msg)
        DEFAULT_LENGTH = 5
        payload = json.dumps(args['payload'])
        # if words is in the request, we should use words code generation
        words_code = False
        if args['words']:
            words_code = True
        data = iAPI.generate_short_url(payload=payload,
                                       endpoint=args['endpoint'],
                                       length=DEFAULT_LENGTH,
                                       words_code=words_code)
        return api_response(data=data)


class resolveShortUrl(Resource):
    """
    API to retrieve a unique short url
    """

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('short_code', type=str, required=True,
                                   help="No short code provided")
        super(resolveShortUrl, self).__init__()

    def get(self):
        try:
            args = self.reqparse.parse_args()
        except Exception as e:
            err_msg = e.data['message']
            all_err = [err_msg[argument] for argument in err_msg.keys()]
            msg = '. '.join(all_err)
            return api_response(code=UNKNOWN_EXCEPTION, message=msg)
        try:
            endpoint, payload = iAPI.get_from_short_code(args['short_code'])
        except ValueError:
            msg = "Short Code does not exist"
            return api_response(code=UNKNOWN_EXCEPTION, message=msg)
        if endpoint == 'path':
            print('path')
            # load dictionary from string
            payload_dict = json.loads(payload)
            labels_dict = {
                'start_label': payload_dict['startLabel'],
                'end_label': payload_dict['endLabel'],
            }
            stop_labels = payload_dict.get('stopLabels', None)
            if stop_labels:
                labels_dict['stop_labels'] = stop_labels
            # options for the search
            search_options = payload_dict['options']
            boat = search_options['boatOptions']
            method = search_options['method']
            if method == "walk":
                mode = "walk"
                walk = search_options['walkingOptions']
                if walk["useAccessibleOptions"]:
                    walk = search_options['accessibleOptions']

            # elif opt["method"] == "accessible":
            #     mode = "walk"
            #     walk = self.accessparse.parse_args(req=opt)
            elif method == "boat":
                mode = "boat"
                walk = boat

            # walk takes different shapes so that later only those
            # parameters are used.
            # we always use walk[speed] but if you are walking walk is walk
            # but if you are by boat walk is boat so walk[speed] is actually
            # boat[speed]
            avoid_bridges = walk["bridgeWeight"] > 1

            try:
                start_coords, end_coords = check_format_coordinates(payload_dict['start'], payload_dict['end'])
                if payload_dict.get('stop', None):
                    stop_coords = check_format_coordinates(payload_dict['stop'])
                else:
                    stop_coords = None
            except (err.CoordinatesFormatError, err.CoordinatesNumberError) as e:
                return api_response(code=e.code)

            ## launch the search
            try:
                #ipdb.set_trace()
                info = iAPI.find_shortest_path_from_coordinates(
                    mode=mode,
                    start=start_coords, end=end_coords, stop=stop_coords,
                    speed=walk["walkSpeed"], avoid_bridges=avoid_bridges,
                    avoid_tide=walk["avoidTide"], tide_level=search_options['tideLevel'],
                    boots_height=walk['bootsHeight'],
                    avoid_public_transport=walk["avoidPublicTransport"],
                    prefer_public_transport=walk["preferPublicTransport"],
                    start_time=search_options["time"],
                    motor=boat["type"] == "motor", boat_speed=boat["boatSpeed"],
                    boat_width=boat["width"], boat_height=boat["height"], boat_draft=boat["draft"],
                    alternatives=search_options.get("alternatives", None)
                )
                final_data = {
                        'data': info,
                        'labels': labels_dict
                    }
                return api_response(data=final_data)
            except Exception as e:
                current_app.logger.error(str(e))
                return api_response(code=getattr(e, 'code', GENERIC_ERROR_CODE))

        elif endpoint == 'search':
            pass


#
#  ██████  ██      ██████       █████  ██████  ██
# ██    ██ ██      ██   ██     ██   ██ ██   ██ ██
# ██    ██ ██      ██   ██     ███████ ██████  ██
# ██    ██ ██      ██   ██     ██   ██ ██      ██
#  ██████  ███████ ██████      ██   ██ ██      ██


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
    @update_api_counter
    def get(self):
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
    @update_api_counter
    def get(self):
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
