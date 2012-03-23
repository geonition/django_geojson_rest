from django.db import models
from django.conf import settings
from django.contrib.gis.db import models as gismodels
from django.contrib.auth.models import User
from django.utils import simplejson as json

class Feature(gismodels.Model):
    """
    This model represents a geographical feature.

    fields:
    geometry -- this is the geometry for the feature
    user -- the user that owns this feature
    group -- the group to which this feature belong to, default is '@self'
    private -- tells the view if this is a private position which should not be shown to others
    create_time -- the time this feature was created
    expire_time -- the time this feature was or will be expired
    """
    geometry = gismodels.GeometryField(srid = getattr(settings, 'SPATIAL_REFERENCE_SYSTEM_ID', 4326))
    user = models.ForeignKey(User)
    group = models.CharField(default = '@self', max_length = 10)
    private = models.BooleanField(default = True)

    create_time = models.DateTimeField(auto_now_add = True)
    expire_time = models.DateTimeField(null = True)

    objects = gismodels.GeoManager()

class Property(models.Model):
    """
    This model represents a property that can be attached to
    a feature or many features.

    This model is supposed to be extended in any appropriate way

    feature -- geographical feature that this property belong to
    user -- the user that added this property
    json_string -- a json that describes the property/properties added
    create_time -- the time this property was created
    expire_time -- the time this property was or will expire
    """
    feature = models.ForeignKey(Feature)
    user = models.ForeignKey(User)
    json_string = models.TextField()

    create_time = models.DateTimeField(auto_now_add=True)
    expire_time = models.DateTimeField(null=True)

