from django.contrib import admin
from django.conf import settings
from models import Feature
from models import Property


class FeatureAdmin(admin.ModelAdmin):
    readonly_fields = ('geometry',
                        'user',
                        'group',
                        'private',
                        'properties',
                        'time')
    

class PropertyAdmin(admin.ModelAdmin):
    readonly_fields = ('user',
                       'group',
                       'json_data',
                       'time')
    
admin.site.register(Feature, FeatureAdmin)
admin.site.register(Property, PropertyAdmin)

