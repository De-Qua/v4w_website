from flask import Flask, url_for, redirect
from flask.logging import default_handler

from config import Config
import sys
import os
import logging
import colorlog
import typing
from logging.handlers import RotatingFileHandler
from flask_sqlalchemy import Model,SQLAlchemy
from flask_migrate import Migrate
import sqlalchemy as sa
from sqlalchemy import MetaData
from flask_mail import Mail
from flask_track_usage import TrackUsage
from flask_track_usage.storage.sql import SQLStorage
from flask_security import Security, SQLAlchemyUserDatastore
from flask_admin import Admin
from flask_security import current_user
from flask_restful import Api
from flask_jwt_extended import JWTManager
from flask_cors import CORS
# from flask_sitemap import Sitemap
# import flask_monitoringdashboard as dashboard

folder = os.getcwd()
folder_db = os.path.join(folder,"app","static","files")
path_graph_street = os.path.join(folder_db,"dequa_ve_terra_v13_1711.gt")
path_graph_water = os.path.join(folder_db,"dequa_ve_acqua_v7_1609_directed.gt")

#
# Create Flask app
#

app = Flask(__name__)
app.config.from_object(Config)

#
# Logging
#
# remove default handler
app.logger.removeHandler(default_handler)
# add handler for the normal console log
color_handler = colorlog.StreamHandler()
formatter = colorlog.ColoredFormatter('[%(asctime)s] [%(name)s:%(filename)s:%(lineno)d] %(log_color)s[%(levelname)s]%(reset)s %(message)s')
color_handler.setFormatter(formatter)
app.logger.addHandler(color_handler)
# add handler for files
if not os.path.exists('logs'):
    os.mkdir('logs')
file_handler = RotatingFileHandler('logs/v4w.log', maxBytes=100000, backupCount=10)
formatter = logging.Formatter('[%(asctime)s] [%(name)s:%(filename)s:%(lineno)d] [%(levelname)s] %(message)s')
file_handler.setFormatter(formatter)
file_handler.setLevel(logging.INFO)
app.logger.addHandler(file_handler)



app.logger.info("Starting the website...")

# version of the software
def getCurrentVersion():
    return app.config.get('VERSION')

__version__ = getCurrentVersion()
app.logger.info(f"Version: {__version__}")

#
# Email setup
#
email = Mail(app)

#
# CORS setup
#
cors = CORS(app, resources={r"/api/*": {"origins": "*"}})

#
# Graph setup
#
from dequa_graph.utils import load_graphs, get_all_coordinates

graph_street, graph_water = load_graphs(path_graph_street, path_graph_water)
# Add graphs info as attributes of the app
app.graphs = {
    'street': {
        'graph': graph_street,
        'all_vertices': get_all_coordinates(graph_street),
    },
    'water': {
        'graph': graph_water,
        'all_vertices': get_all_coordinates(graph_water),
    }
}

#
# Model setup
#
# Crea un modello base per scrivere in modo più leggibile i repr delle classi
class BaseModel(Model):
    def __repr__(self) -> str:
        return self._repr(id=self.id)

    def _repr(self, **fields: typing.Dict[str, typing.Any]) -> str:
        '''
        Helper for __repr__
        '''
        field_strings = []
        at_least_one_attached_attribute = False
        for key, field in fields.items():
            try:
                field_strings.append(f'{key}={field!r}')
            except sa.orm.exc.DetachedInstanceError:
                field_strings.append(f'{key}=DetachedInstanceError')
            else:
                at_least_one_attached_attribute = True
        if at_least_one_attached_attribute:
            return f"<{self.__class__.__name__}({','.join(field_strings)})>"
        return f"<{self.__class__.__name__} {id(self)}>"

#
# Database setup
#
# metadata per magheggio di slalchemy per database sqlite
naming_convention = {
    "ix": 'ix_%(column_0_label)s',
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(column_0_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

# create database for data
db = SQLAlchemy(app,metadata=MetaData(naming_convention=naming_convention),model_class=BaseModel)
migrate = Migrate(app=app,db=db)
#altre magie per sqlalchemy per sqlite
with app.app_context():
    if db.engine.url.drivername == 'sqlite':
        migrate.init_app(app, db, render_as_batch=True)
    else:
        migrate.init_app(app, db)

#
# TrackUsage setup
#
track_datastore = SQLStorage(engine=db.get_engine(bind="collected_data"))
t = TrackUsage(app,[track_datastore])

from app import routes, errors, models
from app.models import Users, Roles, Tokens, TokenTypes, Apis, TokenApiCounters
from app.models import Languages, ErrorGroups, ErrorCodes, ErrorTranslations
from app.models import Area, Location, Neighborhood, Poi, PoiCategory, PoiCategoryType, Street
from app.models import FlaskUsage
from app.models import Ideas
from app.models import Errors, Feedbacks

#
# Users setup
#
user_datastore = SQLAlchemyUserDatastore(db, Users, Roles)
security = Security(app, user_datastore)

#
# Flask-Admin setup
#
admin = Admin(app, name='Admin', base_template='admin_master.html', template_mode='bootstrap4')

from app.views import AdminModelView, UserModelView, RolesModelView
from app.views import TokenModelView, TokenTypeModelView, ApiModelView, TokenApiCounterView
from app.views import UsageModelView, AnalyticsView
from app.views import IdeasModelView
from app.views import StreetModelView, AreaModelView, NeighborhoodModelView, PoiModelView
from app.views import ErrorsModelView
from app.views import FeedbacksModelView, FeedbackVisualizationView
from app.views import ApiErrorLanguageModelView, ApiErrorGroupModelView, ApiErrorCodeModelView, ApiErrorTranslationModelView

admin.add_view(UserModelView(Users, db.session, category="Users"))
admin.add_view(RolesModelView(Roles, db.session, category="Users"))
admin.add_view(TokenModelView(Tokens, db.session, category="Users"))
admin.add_view(TokenTypeModelView(TokenTypes, db.session, category="Users"))
admin.add_view(ApiModelView(Apis, db.session, category="Users"))
admin.add_view(TokenApiCounterView(TokenApiCounters, db.session, category="Users"))
admin.add_view(ApiErrorCodeModelView(ErrorCodes, db.session, category="Error codes"))
admin.add_view(ApiErrorGroupModelView(ErrorGroups, db.session, category="Error codes"))
admin.add_view(ApiErrorTranslationModelView(ErrorTranslations, db.session, category="Error codes"))
admin.add_view(ApiErrorLanguageModelView(Languages, db.session, category="Error codes"))
admin.add_view(StreetModelView(Street, db.session, category="Map"))
admin.add_view(AreaModelView(Area, db.session, category="Map"))
admin.add_view(NeighborhoodModelView(Neighborhood, db.session, category="Map"))
admin.add_view(PoiModelView(Poi, db.session, category="Map"))
admin.add_view(IdeasModelView(Ideas, db.session))
admin.add_view(UsageModelView(FlaskUsage, db.session, category="Usage"))
admin.add_view(AnalyticsView(name='Analytics', endpoint="analytics", category="Usage"))
admin.add_view(ErrorsModelView(Errors, db.session))
admin.add_view(FeedbacksModelView(Feedbacks, db.session, category="Feedback"))
admin.add_view(FeedbackVisualizationView(name="Visualization", endpoint="fb_visualization", category="Feedback"))

#
# Flask Restful API setup
#
api_rest = Api(app, prefix='/api')

from app.src.api import api

api_rest.add_resource(api.getAddress, '/address')
api_rest.add_resource(api.getPath, '/path')
api_rest.add_resource(api.getMultiplePaths, '/multi_path')
api_rest.add_resource(api.getPathStreet, '/gt_path')
api_rest.add_resource(api.getCurrentTide, '/tide')
api_rest.add_resource(api.getSuggestions, '/suggest')

#
# Flask JWT extended
#
jwt = JWTManager(app)

from app.token_helper import is_token_revoked
from app.src.api.utils import api_response
# Define our callback function to check if a token has been revoked or not
@jwt.token_in_blacklist_loader
def check_if_token_revoked(decoded_token):
    return is_token_revoked(decoded_token)

@jwt.revoked_token_loader
def revoked_token_response():
    return api_response(code=3)
#
# Dashboard setup
#
# dashboard.bind(app)

app.logger.info('Website is up')
