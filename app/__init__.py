from flask import Flask, url_for, redirect
from config import Config
import sys
import os
import logging
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
# from flask_sitemap import Sitemap
# import flask_monitoringdashboard as dashboard

#
# Create Flask app
#

app = Flask(__name__)
app.config.from_object(Config)

# version of the software
def getCurrentVersion():
    return app.config.get('VERSION')

__version__ = getCurrentVersion()

#
# Email setup
#
email = Mail(app)


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
track_datastore = SQLStorage(engine=db.get_engine(bind="trackusage"))
t = TrackUsage(app,[track_datastore])

from app import routes, errors, models
from app.models import Users, Roles
from app.models import Area, Location, Neighborhood, Poi, PoiCategory, PoiCategoryType, Street
from app.models import FlaskUsage
from app.models import Ideas

#
# Users setup
#
user_datastore = SQLAlchemyUserDatastore(db, Users, Roles)
security = Security(app, user_datastore)

#
# Flask-Admin setup
#
admin = Admin(app, name='Admin', base_template='admin_master.html', template_mode='bootstrap3')

from app.views import AdminModelView, UsageModelView, StreetModelView, AreaModelView, NeighborhoodModelView, PoiModelView



admin.add_view(UsageModelView(FlaskUsage, db.session))
admin.add_view(AdminModelView(Users, db.session))
admin.add_view(StreetModelView(Street, db.session))
admin.add_view(AreaModelView(Area, db.session))
admin.add_view(NeighborhoodModelView(Neighborhood, db.session))
admin.add_view(PoiModelView(Poi, db.session))

#
# Dashboard setup
#
# dashboard.bind(app)

if not os.path.exists('logs'):
    os.mkdir('logs')
file_handler = RotatingFileHandler('logs/v4w.log', maxBytes=100000, backupCount=10)
file_handler.setFormatter(logging.Formatter(
'%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
file_handler.setLevel(logging.INFO)
app.logger.addHandler(file_handler)

app.logger.info('Setting up the website..')
