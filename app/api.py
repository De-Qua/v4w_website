import pdb

#from flask import abort
from flask_restful import Resource, reqparse, abort
from flask_jwt_extended import jwt_required

from app.src.libpy.lib_search import find_address_in_db
from app.src.interface import find_what_needs_to_be_found


class GetAddressAPI(Resource):
    """
    API to retrieve coordinates from an address
    """

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('address', type=str, required=True,
                                   help="No address provided")
        super(GetAddressAPI, self).__init__()

    @jwt_required
    def get(self):
        args = self.reqparse.parse_args()
        address = args['address']
        try:
            result_dict = find_address_in_db(address)
        except:
            abort(404,
                  error="Address not in the database",
                  message=f"L'indirizzo {address} non è stato trovato nel database")

        return {'coord': result_dict[0]['coordinate']}, 201


class getShortestPath(Resource):
    """
    Api to retrieve the shortest path between two coordinates
    """

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('start', type=str, required=True,
                                   help="No starting point provided")
        self.reqparse.add_argument('end', type=str, required=True,
                                   help="No ending point provided")
        self.reqparse.add_argument('speed', type=float, default=5)
        self.reqparse.add_argument('mode', type=str, default="foot")
        super(getShortestPath, self).__init__()

    @jwt_required
    def get(self):
        args = self.reqparse.parse_args()
        default_params = self.set_default_request_variables()
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

    def set_default_request_variables(self):
        params = {
            'less_bridges': 'off',
            'with_tide': 'off',
            'by_boat': 'off',
            'tide_level': None
        }
        return params
