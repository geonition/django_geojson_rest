from geojson_rest.actions import download_csv
from django.conf import settings
from django.core.urlresolvers import reverse_lazy
from django.contrib import admin
from django.contrib.gis import admin as gisadmin
from django.utils.translation import ugettext_lazy as _
from geojson_rest.models import PointFeature
from geojson_rest.models import LinestringFeature
from geojson_rest.models import PolygonFeature
from geojson_rest.models import Property

class HasFeatureFilter(admin.SimpleListFilter):
    # Human-readable title which will be displayed in the
    # right admin sidebar just above the filter options.
    title = _('is connected to feature')

    # Parameter for the filter that will be used in the URL query.
    parameter_name = 'feature'

    def lookups(self, request, model_admin):
        """
        Returns a list of tuples. The first element in each
        tuple is the coded value for the option that will
        appear in the URL query. The second element is the
        human-readable name for the option that will appear
        in the right sidebar.
        """
        return (
            ('hasfeature', _('is connected to feature')),
            ('nofeature', _('is not connected to feature')),
        )

    def queryset(self, request, queryset):
        """
        Returns the filtered queryset based on the value
        provided in the query string and retrievable via
        `self.value()`.
        """
        # Compare the requested value (either '80s' or 'other')
        # to decide how to filter the queryset.
        if self.value() == 'hasfeature':
            return queryset.exclude(feature=None)
        if self.value() == 'nofeature':
            return queryset.filter(feature=None)
    
class FeatureAdmin(admin.ModelAdmin):
    search_fields = ('user__username', 'group', 'time__create_time')
    list_display = ('user',
                    'group',
                    'get_create_time')
    readonly_fields = ('user',
                       'group',
                       'private',
                       'properties',
                       'time')
    list_filter = ('group', 'private',)
    #date_hierarchy = ('time__create_time')
    actions = [download_csv]
    modifiable = False
    
    def __str__(self):
        return "Feature"

class PointFeatureAdmin(gisadmin.OSMGeoAdmin, FeatureAdmin):
    """
    This is subclass for FeatureAdmin but handles only
    point geometries.
    """
    
    openlayers_url = '%s%s' % (getattr(settings, 'STATIC_URL', '/'),
                               'js/libs/OpenLayers.js')
    extra_js = (reverse_lazy('osmextra'),)
    actions = ['delete_selected_places']

    def get_actions(self, request):
        actions = super(PointFeatureAdmin, self).get_actions(request)
        del actions['delete_selected']
        return actions

    def delete_selected_places(self, request, queryset):
        for obj in queryset:
            obj.delete()

        self.message_user(request, _("successfully deleted places."))
    
    delete_selected_places.short_description = _('delete selected places')
    
    def queryset(self, request):
        return self.model.objects.all()
        
admin.site.register(PointFeature, PointFeatureAdmin)

class LinestringFeatureAdmin(gisadmin.OSMGeoAdmin, FeatureAdmin):
    """
    This is subclass for FeatureAdmin but handles only
    linestring geometries.
    """
    
    openlayers_url = '%s%s' % (getattr(settings, 'STATIC_URL', '/'),
                               'js/libs/OpenLayers.js')
    extra_js = (reverse_lazy('osmextra'),)
    actions = ['delete_selected_routes']

    def get_actions(self, request):
        actions = super(LinestringFeatureAdmin, self).get_actions(request)
        del actions['delete_selected']
        return actions

    def delete_selected_routes(self, request, queryset):
        for obj in queryset:
            obj.delete()

        self.message_user(request, _("successfully deleted routes."))
    
    delete_selected_routes.short_description = _('delete selected routes')
    
    def queryset(self, request):
        return self.model.objects.all()
        
admin.site.register(LinestringFeature, LinestringFeatureAdmin)

class PolygonFeatureAdmin(gisadmin.OSMGeoAdmin, FeatureAdmin):
    """
    This is subclass for FeatureAdmin but handles only
    polygon geometries.
    """
    
    openlayers_url = '%s%s' % (getattr(settings, 'STATIC_URL', '/'),
                               'js/libs/OpenLayers.js')
    extra_js = (reverse_lazy('osmextra'),)
    actions = ['delete_selected_areas']

    def get_actions(self, request):
        actions = super(PolygonFeatureAdmin, self).get_actions(request)
        del actions['delete_selected']
        return actions

    def delete_selected_routes(self, request, queryset):
        for obj in queryset:
            obj.delete()

        self.message_user(request, _("successfully deleted areas."))
    
    delete_selected_routes.short_description = _('delete selected areas')
    
    def queryset(self, request):
        return self.model.objects.all()
        
admin.site.register(PolygonFeature, PolygonFeatureAdmin) 

class PropertyAdmin(admin.ModelAdmin):
    search_fields = ('user__username', 'group', 'time__create_time')
    list_display = ('group',
                    'user',
                    'get_create_time',
                    'json_data')
    readonly_fields = ('user',
                       'group',
                       'json_data',
                       'time')
    list_filter = ('group', HasFeatureFilter, )
    actions = [download_csv]
        
    def __str__(self):
        return "Property"
    

admin.site.register(Property, PropertyAdmin)

