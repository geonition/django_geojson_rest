from django.db import models
from django.conf import settings
from django.contrib.gis.db import models as gismodels
from django.contrib.auth.models import User
from django.utils import simplejson as json
from geonition_utils.models import JSON
from geonition_utils.models import TimeD

class Property(models.Model):
    """
    This model represents a property that can be attached to
    a feature or many features.

    This model is supposed to be extended in any appropriate way

    feature -- geographical feature that this property belong to
    user -- the user that added this property
    json_data -- foreignkey to the json data model
    time -- foreignkey to the time model
    """
    user = models.ForeignKey(User)
    
    json_data = models.OneToOneField(JSON)

    time = models.OneToOneField(TimeD)

class Feature(gismodels.Model):
    """
    This model represents a geographical feature.

    fields:
    geometry -- this is the geometry for the feature
    user -- the user that owns this feature
    group -- the group to which this feature belong to, default is '@self'
    private -- tells the view if this is a private position which should not be shown to others
    time -- foreignkey to the time model
    """
    geometry = gismodels.GeometryField(srid = getattr(settings, 'SPATIAL_REFERENCE_SYSTEM_ID', 4326))
    user = models.ForeignKey(User)
    group = models.CharField(default = '@self', max_length = 10)
    private = models.BooleanField(default = True)
    properties = models.ManyToManyField(Property)
    time = models.OneToOneField(TimeD)

    objects = gismodels.GeoManager()
    
    
    def create_feature(self, geojson_feature):
        user_id = geojson_feature['properties']['user_id']
        geos = OGRGeometry(json.dumps(geometry)).geos
        
        new_time = TimeD()
        new_time.save()
        
        new_property = Property()
