from flask import Flask
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

# version of the software
version = "0.1"

app = Flask(__name__)
app.config.from_object(Config)
#function to retrieve the version
def getCurrentVersion():
    return version
# metadata per magheggio di slalchemy per database sqlite
naming_convention = {
    "ix": 'ix_%(column_0_label)s',
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(column_0_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}
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

db = SQLAlchemy(app,metadata=MetaData(naming_convention=naming_convention),model_class=BaseModel)
migrate = Migrate(app=app,db=db)
#altre magie per sqlalchemy per sqlite
with app.app_context():
    if db.engine.url.drivername == 'sqlite':
        migrate.init_app(app, db, render_as_batch=True)
    else:
        migrate.init_app(app, db)
from app import routes, errors, models

if not os.path.exists('logs'):
    os.mkdir('logs')
file_handler = RotatingFileHandler('logs/v4w.log', maxBytes=100000, backupCount=10)
file_handler.setFormatter(logging.Formatter(
'%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
file_handler.setLevel(logging.INFO)
app.logger.addHandler(file_handler)

app.logger.info('Setting up the website..')
