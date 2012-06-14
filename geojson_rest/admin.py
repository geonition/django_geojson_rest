from actions import download_csv
from django.conf import settings
from django.contrib import admin
from django.utils.translation import ugettext_lazy as _
from models import Feature
from models import Property

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
    readonly_fields = ('geometry',
                        'user',
                        'group',
                        'private',
                        'properties',
                        'time')
    list_filter = ('group', 'private', )
    actions = [download_csv]
    

class PropertyAdmin(admin.ModelAdmin):
    readonly_fields = ('user',
                       'group',
                       'json_data',
                       'time')
    list_filter = ('group', HasFeatureFilter, )
    actions = [download_csv]


admin.site.register(Feature, FeatureAdmin)
admin.site.register(Property, PropertyAdmin)

