from flask import redirect, url_for
from flask_security import current_user
from flask_admin.contrib.sqla import ModelView

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

class UsageModelView(AdminModelView):
    def is_accessible(self):
        return (current_user.has_role('admin'))

class StreetModelView(AdminModelView):
    def is_accessible(self):
        return (current_user.has_role('admin'))
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
    column_filters = ['types', 'score', 'opening_hours', 'wheelchair', 'toilets',
                'toilets_wheelchair', 'atm']
    column_editable_list = ['types', 'score', 'opening_hours', 'wheelchair', 'toilets',
                'toilets_wheelchair', 'atm']
    column_exclude_list = ['osm_type', 'osm_id']
    column_editable_list = ['name_alt', 'score']
