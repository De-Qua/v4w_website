from app.views import AdminModelView

class CurrentDataModelView(AdminModelView):
    column_list = ('id', 'street_graph_id', 'waterbus_graph_id', 'water_graph_id', 'tide_id', 'graph_updated_at', 'graph_check_at')

class GraphStreetModelView(AdminModelView):
    column_list = ('id', 'name', 'version', 'created_at')
    form_excluded_columns = ('data', 'waterbus_graphs')  # large binary + relationship
    column_searchable_list = ('name',)
    column_filters = ('version', 'created_at')

class GraphWaterbusModelView(AdminModelView):
    column_list = ('id', 'name', 'gtfs_number', 'valid_from', 'valid_to', 'graphstreet_id')
    form_excluded_columns = ('data',)
    column_searchable_list = ('name',)
    column_filters = ('valid_from', 'valid_to', 'gtfs_number')

class GraphWaterModelView(AdminModelView):
    column_list = ('id', 'name', 'version', 'created_at')
    form_excluded_columns = ('data',)
    column_searchable_list = ('name',)
    column_filters = ('version', 'created_at')

class TideModelView(AdminModelView):
    column_list = ('id', 'station', 'short_name', 'latDMSN', 'lonDMSE', 'value', 'updated_at', 'uploaded_at')
    column_searchable_list = ('station', 'short_name')
    column_filters = ('updated_at', 'uploaded_at', 'id_station')
