from django.contrib.gis import admin as gis_admin
from django.contrib import admin
from models import Feature
from models import Property
from django.contrib.gis.utils import add_postgis_srs

add_postgis_srs(900913)
admin.site.register(Feature, gis_admin.OSMGeoAdmin)
admin.site.register(Property, admin.ModelAdmin)

