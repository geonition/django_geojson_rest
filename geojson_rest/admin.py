from actions import download_csv
from django.conf import settings
from django.conf.urls.defaults import patterns
from django.contrib import admin
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils.translation import ugettext_lazy as _
from models import Feature
from models import Property
import json

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
    search_fields = ('user', 'group',)
    list_display = ('user',
                    'group',
                    'view_geometry_link')
    readonly_fields = ('geometry',
                       'user',
                       'group',
                       'private',
                       'properties',
                       'time')
    list_filter = ('group', 'private',)
    actions = [download_csv]
    
    def get_urls(self):
        urls = super(FeatureAdmin, self).get_urls()
        
        extra_urls = patterns('',
                            (r'^view_geometry$', self.admin_site.admin_view(self.view_geometry)),
                            )
        return extra_urls + urls
    
    def view_geometry_link(self, obj):
        return '<a href="view_geometry?id=%d">view geometry</a>' % obj.id
    
    view_geometry_link.allow_tags = True
        
    def view_geometry(self, request):
        feature_id = request.GET.get('id')
        feature = Feature.objects.get(pk = feature_id)
        feature_dict = feature.to_json()
        feature_json = json.dumps(feature_dict)
        return render_to_response('admin/geojson_rest/feature/view_features.html',
                                  {'feature': feature,
                                   'feature_json': feature_json,
                                   'srid': getattr(settings, 'SPATIAL_REFERENCE_SYSTEM_ID', 4326)},
                                  context_instance = RequestContext(request))
    
    def __str__(self):
        return "Feature"
    

class PropertyAdmin(admin.ModelAdmin):
    list_display = ('group',
                    'json_data',
                    'user',)
    readonly_fields = ('user',
                       'group',
                       'json_data',
                       'time')
    list_filter = ('group', HasFeatureFilter, )
    actions = [download_csv]
        
    def __str__(self):
        return "Property"
    

admin.site.register(Feature, FeatureAdmin)
admin.site.register(Property, PropertyAdmin)

