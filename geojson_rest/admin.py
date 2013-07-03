from geojson_rest.actions import download_csv
from django.conf import settings
from django.core.urlresolvers import reverse_lazy
from django.contrib import admin
from django.contrib.gis import admin as gisadmin
from django.utils.translation import ugettext_lazy as _
# from geojson_rest.models import PointFeature
# from geojson_rest.models import LinestringFeature
# from geojson_rest.models import PolygonFeature
from geojson_rest.models import Feature
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
    
class FeatureAdmin(gisadmin.OSMGeoAdmin):
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
    openlayers_url = '%s%s' % (getattr(settings, 'STATIC_URL', '/'),
                               'js/libs/OpenLayers.js')
    actions = [download_csv]
    modifiable = False
    actions = ['delete_selected']
    

    def delete_selected(self, request, queryset):
        for obj in queryset:
            obj.delete()
 
        self.message_user(request, _("successfully deleted the selected features."))
     
    delete_selected.short_description = _('delete selected features')
    def __str__(self):
        return "Feature"

admin.site.register(Feature, FeatureAdmin)


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

