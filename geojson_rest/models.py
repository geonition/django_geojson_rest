from django.db import models
from django.core.urlresolvers import reverse
from django.conf import settings
from django.contrib.gis.db import models as gismodels
#from django.contrib.gis.gdal import OGRGeometry
from django.contrib.gis.geos import GEOSGeometry
from django.contrib.auth.models import User
from django.utils import simplejson as json
from django.utils.translation import ugettext_lazy as _
from geonition_utils.models import JSON
from geonition_utils.models import TimeD

from shapely.geometry import asShape

class Property(models.Model):
    """
    This model represents a property that can be attached to
    a feature or many features.

    This model is supposed to be extended in any appropriate way

    feature -- geographical feature that this property belong to
    user -- the user that added this property
    group -- the group the property belong to, should be the same as the
             features that the property might be connected to
    json_data -- foreignkey to the json data model
    time -- foreignkey to the time model
    """
    user = models.ForeignKey(User)
    group = models.CharField(default = '@self',
                             max_length = 50)
    
    json_data = models.OneToOneField(JSON)
    time = models.OneToOneField(TimeD)

    def create(self, properties, *args, **kwargs):
        """
        This function saves properties of the feature,
        """
        js = JSON(json_string = json.dumps(properties),
                  collection = 'properties')
        js.save()
        self.json_data = js
        timed = TimeD()
        timed.save()
        self.time = timed
        super(Property, self).save(*args, **kwargs)

    def update(self, properties, *args, **kwargs):
        new_json = json.loads(self.json_data.json_string)
        new_json.update(properties)
        self.json_data.json_string = json.dumps(new_json)
        self.json_data.save()

    def to_json(self):
        if self.time.expire_time == None:
            exrtime = ''
        else:
            exrtime = self.time.expire_time.isoformat()

        retval = self.json_data.json()
        retval.update({'time': {'create_time': self.time.create_time.isoformat(),
                                'expire_time': exrtime},
                        'user': self.user.username,
                        'id': self.id,
                        'group': self.group })
        return retval

    def delete(self, *args, **kwargs):
        super(Property, self).delete()
    
    
    def __unicode__(self):
        return u'%i %s %s' % (self.id, self.group, self.user)
        
    class Meta:
        unique_together = ('json_data', 'user', 'time')
        permissions = (
                ('can_view_private', 'Can view private properties'),
                )


class FeatureBase(gismodels.Model):
    """
    This model represents a geographical feature.

    fields:
    geometry -- this is the geometry for the feature
    user -- the user that owns this feature
    group -- the group to which this feature belong to, default is '@self'
    private -- tells the view if this is a private position which should not be shown to others
    time -- foreignkey to the time model
    """
    user = models.ForeignKey(User)
    group = models.CharField(default = '@self', max_length = 50)
    private = models.BooleanField(default = True)
    time = models.OneToOneField(TimeD)

    objects = gismodels.GeoManager()

    def get_properties(self):
        """
        This function returnes all the properties.

        overrides keys so be sure to save them in a way that
        that does not happen..
        """
        property_entities = self.properties.all()
        properties = {}
        for prop in property_entities:
            properties.update(prop.to_json())

        return properties

    def to_json(self):
        """
        This function return a dictionary representation
        of this object.
        """
        if self.time.expire_time == None:
            exrtime = ''
        else:
            exrtime = self.time.expire_time.isoformat()

        json_obj = {
            'id': self.id,
            'private': self.private,
            'geometry': json.loads(self.geometry.json),
            'properties': self.get_properties(),
            'type': 'Feature',
            'time': {'create_time': self.time.create_time.isoformat(),
                     'expire_time': exrtime},
            'user': self.user.username,
            'group': self.group
        }

        return json_obj
    
    def get_absolute_url(self):
        return '%s/@all/@all/%i' % (reverse('feat'), self.id)
        
    def __unicode__(self):
        return u'%i %s %s' % (self.id, self.group, self.user)
    
    class Meta:
        abstract = True
        permissions = (
                ('can_view_private', 'Can view private features'),
                )
    

class Feature(FeatureBase):
    """
    this inherits form base and is the model
    that should be used for crud functionality
    """
    geometry = gismodels.GeometryField(srid = getattr(settings, 'SPATIAL_REFERENCE_SYSTEM_ID', 4326))
    properties = models.ManyToManyField(Property)

    def create(self, feature, *args, **kwargs):
        """
        This function creates a feature which is a
        python dict representation of a geojson object.

        The feature properties like create_time or
        expire time should be given in the feature object
        e.g.
        {
        "type": "Feature",
        "geometry": ...,
        "properties": ...,
        "id": ...,
        "private": ...,
        "time": ...,
        "user": ...,
        "group": ...
        }
        """
        #TODO do not use GDAL
#        self.geometry = OGRGeometry(json.dumps(feature['geometry'])).geos
#        self.geometry = GEOSGeometry(json.dumps(feature['geometry']))
        # There is a problem with GDAL from_json routine
        # so we use shapely library to circumvent the problem.
        temp_geom = asShape(feature['geometry'])
        self.geometry = GEOSGeometry(temp_geom.to_wkt())
        self.private = feature.get('private', True)
        timed = TimeD()
        timed.save()
        self.time = timed
        prop = Property(user = self.user,
                        group = self.group)
        prop.create(feature['properties'])
        super(Feature, self).save(*args, **kwargs)
        self.properties.add(prop)

    def update(self, feature, user, *args, **kwargs):
        """
        This function updates the feature, user indicates
        the user updating the feature.

        only some values can be updated:
        private -- can be updated by the creator of the feature
        properties -- can be updated by all (saved separate per user)
        """
        if self.user == user:
            self.private = feature.get('private', True)
            old_property = self.properties.get(user = user)
            old_property.update(feature['properties'])
            self.save(*args, **kwargs)
        else:
            try:
                old_property = self.properties.get(user = user)
                old_property.update(feature['properties'])
            except Property.DoesNotExist:
                prop = Property(user = user,
                                group = self.group)
                prop.create(feature['properties'], user)
                self.properties.add(prop)

#geometry models inherited form generic Feature
class PointFeature(FeatureBase):
    """
    This model handle the point features
    
    This is a not managed database class and
    requires a view to be made in the database.
    The view creation sql is in the
    sql/feature.sql file.
    """
    geometry = gismodels.PointField(srid = getattr(settings, 'SPATIAL_REFERENCE_SYSTEM_ID', 4326))
    properties = models.ManyToManyField(Property,
                                        through = 'PointFeatureProperty')
    
    # no adding or deleting allowed for DB views
    def has_add_permission(self, request, obj=None):
        return False
    def has_delete_permission(self, request, obj=None):
        return False
    
    #this is for superusers
    def delete(self, *args, **kwargs):
        Feature.objects.get(id = self.id).delete()
        
    class Meta:
        managed = False
        db_table = 'pointfeature'
        verbose_name = _('place')
        verbose_name_plural = _('places')
        
#hack to handle manytomanyfields in database views and django ORM
class PointFeatureProperty(models.Model):
    feature = models.ForeignKey(PointFeature)
    property = models.ForeignKey(Property)
    
    # no adding or deleting allowed for DB views
    def has_add_permission(self, request, obj=None):
        return False
    def has_delete_permission(self, request, obj=None):
        return False
    
    #this is for superusers
    def delete(self, *args, **kwargs):
        Property.objects.get(id = self.id).delete()
    
    class Meta:
        managed = False
        db_table = 'pointfeatureproperty'
        verbose_name = _('place property')
        verbose_name_plural = _('place properties')

class LinestringFeature(FeatureBase):
    """
    This model handle the linestring features
    
    This is a not managed database class and
    requires a view to be made in the database.
    The view creation sql is in the
    sql/feature.sql file.
    """
    geometry = gismodels.LineStringField(srid = getattr(settings, 'SPATIAL_REFERENCE_SYSTEM_ID', 4326))
    properties = models.ManyToManyField(Property,
                                        through = 'LinestringFeatureProperty')
    
    # no adding or deleting allowed for DB views
    def has_add_permission(self, request, obj=None):
        return False
    def has_delete_permission(self, request, obj=None):
        return False
    
    #this is for superusers
    def delete(self, *args, **kwargs):
        Feature.objects.get(id = self.id).delete()
    
    class Meta:
        managed = False
        db_table = 'linestringfeature'
        verbose_name = _('route')
        verbose_name_plural = _('routes')

#hack to handle manytomanyfields in database views and django ORM
class LinestringFeatureProperty(models.Model):
    feature = models.ForeignKey(LinestringFeature)
    property = models.ForeignKey(Property)
    
    # no adding or deleting allowed for DB views
    def has_add_permission(self, request, obj=None):
        return False
    def has_delete_permission(self, request, obj=None):
        return False
    
    class Meta:
        managed = False
        db_table = 'linestringfeatureproperty'
        verbose_name = _('route property')
        verbose_name_plural = _('route properties')
        
class PolygonFeature(FeatureBase):
    """
    This model handle the polygon features
    
    This is a not managed database class and
    requires a view to be made in the database.
    The view creation sql is in the
    sql/feature.sql file.
    """
    geometry = gismodels.PolygonField(srid = getattr(settings, 'SPATIAL_REFERENCE_SYSTEM_ID', 4326))
    properties = models.ManyToManyField(Property,
                                        through = 'PolygonFeatureProperty')
    
    # no adding or deleting allowed for DB views
    def has_add_permission(self, request, obj=None):
        return False
    def has_delete_permission(self, request, obj=None):
        return False
    
    #this is for superusers
    def delete(self, *args, **kwargs):
        Feature.objects.get(id = self.id).delete()
    
    class Meta:
        managed = False
        db_table = 'polygonfeature'
        verbose_name = _('area')
        verbose_name_plural = _('areas')
        
#hack to handle manytomanyfields in database views and django ORM
class PolygonFeatureProperty(models.Model):
    feature = models.ForeignKey(PolygonFeature)
    property = models.ForeignKey(Property)
    
    # no adding or deleting allowed for DB views
    def has_add_permission(self, request, obj=None):
        return False
    def has_delete_permission(self, request, obj=None):
        return False
    
    class Meta:
        managed = False
        db_table = 'polygonfeatureproperty'
        verbose_name = _('area property')
        verbose_name_plural = _('area properties')
