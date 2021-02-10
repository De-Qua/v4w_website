from datetime import datetime

from flask import redirect, url_for
from flask_security import current_user, utils
from flask_admin.contrib.sqla import ModelView
import app.src.interface as interface
from flask_admin import BaseView, expose

from app.token_helper import create_new_token
###
# MODELS FOR ADMIN VIEWS
###
class AdminModelView(ModelView):
    def is_accessible(self):
        return (current_user.is_active and current_user.is_authenticated)
    def _handle_view(self, name):
        if not self.is_accessible():
            return redirect(url_for('security.login'))
    can_edit = True

class UserModelView(AdminModelView):
    column_list = ['email', 'roles', 'active', 'confirmed_at']
    column_exclude_list = ['password']
    column_editable_list = ['active']
    form_excluded_columns = ['tokens', 'confirmed_at']
    # column_hide_backrefs = False

    def on_model_change(self, form, model, is_created):
        model.password = utils.hash_password(model.password)
        if model.active:
            model.confirmed_at = datetime.now()
        else:
            model.confirmed_at = None

class RolesModelView(AdminModelView):
    column_list = ['name', 'description']
    form_excluded_columns = ['user']
    # column_hide_backrefs = False
    def is_accessible(self):
        return (current_user.is_active and current_user.is_authenticated)
    def _handle_view(self, name):
        if not self.is_accessible():
            return redirect(url_for('security.login'))

class TokenModelView(AdminModelView):
    column_list = ['user', 'type', 'revoked', 'expires', 'token']
    column_editable_list = ['revoked']
    form_excluded_columns = ['jti', 'token', 'api', 'api_counter']
    can_edit = False

    def on_model_change(self, form, model, is_created):
        if is_created:
            token_info = create_new_token(model.user, model.type, model.expires)
            model.jti = token_info['jti']
            model.token = token_info['token']


class TokenTypeModelView(AdminModelView):
    column_list = ['type', 'permissions']
    column_editable_list = ['type', 'permissions']
    form_excluded_columns = ['tokens']


class ApiErrorLanguageModelView(AdminModelView):
    column_list = ['code', 'name']
    form_excluded_columns = ['translations']


class ApiErrorGroupModelView(AdminModelView):
    column_list = ['name', 'codes']


class ApiErrorCodeModelView(AdminModelView):
    column_list = ['code', 'description', 'group']
    form_excluded_columns = ['translations']
    column_editable_list = ['description']


class ApiErrorTranslationModelView(AdminModelView):
    column_list = ['code', 'language', 'message']
    column_editable_list = ['message']


class ApiModelView(AdminModelView):
    column_list = ['name', 'path']
    form_excluded_columns = ['token', 'api_counter']


class TokenApiCounterView(AdminModelView):
    column_list = ['token.user', 'api', 'count']
    column_filters = ['token.user', 'api.name']


class UsageModelView(AdminModelView):
    column_default_sort = ('datetime', True)
    column_searchable_list = ['url', 'ua_browser', 'path', 'track_var']
    column_exclude_list = ['blueprint', 'view_args', 'status', 'remote_addr',
                           'xforwardedfor', 'authorization', 'ip_info']
    column_filters = ['url', 'ua_browser', 'ua_language', 'path', 'track_var']
    can_edit = False

class AnalyticsView(BaseView):
    @expose('/')
    def index(self):
        usage_data = interface.get_usage_data_from_server()
        return self.render('admin/new_charts.html', usage_dict=usage_data)
    def is_accessible(self):
        return (current_user.is_active and current_user.is_authenticated)
    def _handle_view(self, name):
        if not self.is_accessible():
            return redirect(url_for('security.login'))

class StreetModelView(AdminModelView):
    column_searchable_list = ['name', 'name_alt']
    column_editable_list = ['name_alt', 'score']
    column_exclude_list = ['shape']
    column_filters = ['name_alt','name_spe', 'name_den', 'score', 'neighborhoods', 'areas']


class AreaModelView(AdminModelView):
    column_searchable_list = ['name']
    column_filters = ['streets']
    column_exclude_list = ['shape']

class NeighborhoodModelView(AdminModelView):
    def is_accessible(self):
        return (current_user.has_role('admin'))
    column_searchable_list = ['name']
    column_filters = ['zipcode']
    column_exclude_list = ['shape']

class PoiModelView(AdminModelView):
    column_searchable_list = ['name', 'name_alt', 'wikipedia', 'phone', 'osm_other_tags']
    column_filters = ['name', 'name_alt', 'types', 'score', 'opening_hours', 'wheelchair', 'toilets',
                'toilets_wheelchair', 'atm']
    column_editable_list = ['types', 'score', 'opening_hours', 'wheelchair', 'toilets',
                'toilets_wheelchair', 'atm']
    column_exclude_list = ['osm_type', 'osm_id']
    column_editable_list = ['name_alt', 'score']

class IdeasModelView(AdminModelView):
    column_default_sort = ('num_of_votes', True)

class ErrorsModelView(AdminModelView):
    column_default_sort = ('datetime', True)
    column_editable_list = ['solved']
    column_filters = ['datetime', 'method', 'error_type', 'url', 'browser', 'solved']
    column_searchable_list = ['method', 'error_type', 'error_message',
                            'url', 'method', 'browser']


class FeedbacksModelView(AdminModelView):
    column_default_sort = ('datetime', True)
    column_editable_list = ['solved']
    column_filters = ['datetime', 'version', 'category', 'solved']
    column_searchable_list = ['version', 'category',
                              'searched_string', 'searched_start', 'searched_end',
                              'found_string', 'found_start', 'found_end',
                              'feedback']
    column_exclude_list = ['json']

class FeedbackVisualizationView(BaseView):
    @expose('/')
    def index(self):
        feedback_dict = interface.get_feedback_from_server()
        return self.render('admin/feedback.html', feedback_dict = feedback_dict)
    def is_accessible(self):
        return (current_user.is_active and current_user.is_authenticated)
    def _handle_view(self, name):
        if not self.is_accessible():
            return redirect(url_for('security.login'))
