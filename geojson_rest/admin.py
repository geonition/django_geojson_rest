from django.contrib.gis import admin as gis_admin
from django.contrib import admin
from models import Feature
from models import Property

admin.site.register(Feature, gis_admin.OSMGeoAdmin)
admin.site.register(Property, admin.ModelAdmin)

