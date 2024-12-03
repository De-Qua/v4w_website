from app import app, db, user_datastore, security, admin
from app.models import Location, Street, Neighborhood, Poi, Apis, TokenTypes
from app.src.api.api import AVAILABLE_APIS
from flask_admin import helpers as admin_helpers
from flask import url_for
from flask_security import utils
from dotenv import load_dotenv
import os

# load DEQUA_SECRETS
load_dotenv('DEQUA_SECRETS.env')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD')
SOMEONE_PASSWORD = os.getenv('SOMEONE_PASSWORD')

@app.shell_context_processor
def make_shell_context():
    return {"db": db,
    "Location": Location,
    "Street": Street,
    "Neighborhood": Neighborhood,
    "Poi": Poi}

# Create the tables for the users and roles and add a user to the user table
# This decorator registers a function to be run before the first request to the app
#  i.e. calling localhost:5000 from the browser
# @app.before_first_request
# def before_first_request():
#     if app.debug:
#         # Create any database tables that don't exist yet.
#         app.logger.debug("Before first request")
#         db.create_all(bind='internal')
#         create_first_user_role(db.session)
#         app.logger.debug("User created")
#         create_all_api(db.session)
#         app.logger.debug("Api created")
#         create_admin_token(db.session)
#         app.logger.debug("Admin token created")


def create_all_api(session):
    # loop and create api if the endpoint does not exist
    for function, info in AVAILABLE_APIS.items():
        endpoint_api = Apis.query.filter_by(path=info['endpoint']).one_or_none()
        if not endpoint_api:
            endpoint_api = Apis(name=info["name"], path=info["endpoint"])
            session.add(endpoint_api)
            session.commit()


def create_admin_token(session):
    # create or update the role admin for the tokens
    admin_role = TokenTypes.query.filter_by(type="admin").one_or_none()
    if not admin_role:
        admin_role = TokenTypes(type="admin")
        session.add(admin_role)
    for an_api in Apis.query.all():
        if an_api not in admin_role.permissions:
            admin_role.permissions.append(an_api)
    session.commit()


def create_first_user_role(session):
    # Create the Roles "admin" and "end-user" -- unless they already exist
    user_datastore.find_or_create_role(name='admin', description='Administrator')
    user_datastore.find_or_create_role(name='end-user', description='End user')

    # Create two Users for testing purposes -- unless they already exists.
    # In each case, use Flask-Security utility function to encrypt the password.
    someone_password = SOMEONE_PASSWORD
    admin_password = ADMIN_PASSWORD
    if not user_datastore.get_user('someone'):
        user_datastore.create_user(email='someone', password=utils.hash_password(someone_password))
    if not user_datastore.get_user('admin'):
        user_datastore.create_user(email='admin', password=utils.hash_password(admin_password))

    # Commit any database changes; the User and Roles must exist before we can add a Role to the User
    session.commit()

    # Give one User has the "end-user" role, while the other has the "admin" role. (This will have no effect if the
    # Users already have these Roles.) Again, commit any database changes.
    user_datastore.add_role_to_user('someone', 'end-user')
    user_datastore.add_role_to_user('admin', 'admin')
    session.commit()

# Include security variable to admin views
@security.context_processor
def security_context_processor():
    return dict(
        admin_base_template = admin.base_template,
        admin_view = admin.index_view,
        h = admin_helpers,
        get_url = url_for
    )
