import pdb
#from flask import abort
from flask_restful import Resource, reqparse, abort
from flask_jwt_extended import jwt_required

from app.src.libpy.lib_search import find_address_in_db


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
