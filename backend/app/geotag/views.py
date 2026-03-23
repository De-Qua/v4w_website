from app.views import AdminModelView

###
# GEOTAG MODELS
###

class LanguageModelView(AdminModelView):
    column_list = ['name','code','order']
    form_columns = ['name','code','order']

class NameOnlyModelView(AdminModelView):
    column_list = ['name']
    form_columns = ['name']

class GeouserModelView(AdminModelView):
    # column_list = ['name', 'name_alt', 'name_spe', 'name_den', 'neighborhood', 'score']
    # column_searchable_list = ['name', 'name_alt']
    # column_editable_list = ['name_alt', 'score']
    column_list = ['name','email','nickname','active','confirmed_at']
    column_searchable_list = ['name','email','nickname']
    form_columns = ['name','email','nickname','password','active','confirmed_at']
    # column_filters = ['name_alt','name_spe', 'name_den', 'score', 'neighborhood']
    # not anymore in postgres, they are automatically binded but not columns
    # , 'neighborhoods', 'areas']

class TagModelView(AdminModelView):
    column_list = ['creator', 'name']
    form_columns = ['creator', 'name']

class DatagroupModelView(AdminModelView):
    column_list = ['name', 'keyname', 'owner']
    form_columns = ['owner', 'name', 'keyname']

class LayerModelView(AdminModelView):
    column_list = ['name', 'url', 'date_creation', 'date_start', 'date_end', 'date_last_modification', 'active', 'default_icon', 'owner', 'default_language', 'visibility', 'contribution', 'tags', 'datagroups']
    column_searchable_list = ['name']
    column_filters = ['active', 'owner', 'default_language', 'visibility', 'contribution', 'date_start', 'date_end']
    form_columns = ['owner', 'name', 'tags', 'datagroups','url', 'date_creation', 'date_start', 'date_end', 'date_last_modification', 'active', 'default_icon', 'default_language', 'visibility', 'password', 'contribution']

class LayerItemModelView(AdminModelView):
    column_list = ['owner','layer','datagroup','lat','lng','icon','tags','active','approved','date_creation','date_start','date_end']
    form_columns = ['owner','layer','datagroup','lat','lng','icon','tags','active','approved','date_creation','date_start','date_end']

class LayerItemDatagroupParameterModelView(AdminModelView):
    column_list = ['keyname', 'datatype', 'datagroup']
    form_columns = ['keyname', 'datatype', 'datagroup']


# class AreaModelView(AdminModelView):
#     column_searchable_list = ['name']
#     column_filters = ['streets']
#     column_exclude_list = ['shape']

