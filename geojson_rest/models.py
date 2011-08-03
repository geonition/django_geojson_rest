from django.db import models
from django.contrib.gis.db import models as gis_models
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from manager import MongoDBManager
from pymongo import Connection

import datetime
import settings
import sys

if sys.version_info >= (2, 6):
    import json
else:
    import simplejson as json

#this can be used instead of writing getattr everywhere
USE_MONGODB = getattr(settings, "USE_MONGODB", False)


# Create your models herelas   
# GEOMETRY MODELS
class Feature(gis_models.Model):
    """
    A Feature is defined by structure as a geojson feature
    containing a geometry object and has properties in
    the Property model.
    
    >>> u = User.objects.create_user('test-feature','')
    >>> f = Feature(geometry = 'POINT(2 3)', user = u)
    >>> f.expire_time
    >>> f.create_time
    >>> f.save()
    >>> type(f.create_time)
    <type 'datetime.datetime'>
    >>> from django.contrib.gis.gdal import OGRGeometry
    >>> geos = OGRGeometry(json.dumps({'type':'point', 'coordinates': [2, 3]})).geos
    >>> f_temp = f.update(geometry = geos) #same geom should not update
    >>> f_temp.id == f.id
    True
    >>> geos = OGRGeometry(json.dumps({'type':'point', 'coordinates': [4, 4]})).geos
    >>> f_temp = f.update(geometry = geos) #different geom should update
    >>> f_temp.id == f.id
    False
    >>> type(f.expire_time) #update should have expired this
    <type 'datetime.datetime'>
    >>> f2 = Feature.objects.get(id = f.id)
    >>> f2.expire_time == f.expire_time
    True
    >>> type(f_temp.expire_time) #the current feature should not be expired
    <type 'NoneType'>
    >>> f_temp.delete()
    >>> type(f_temp.expire_time)
    <type 'datetime.datetime'>
    """
    geometry = gis_models\
                .GeometryField(srid=settings.SPATIAL_REFERENCE_SYSTEM_ID)
    user = models.ForeignKey(User)
    
    create_time = models.DateTimeField(auto_now_add=True, null=True)
    expire_time = models.DateTimeField(null=True)
    
    objects = gis_models.GeoManager()
    
    def delete(self, *args, **kwargs):
        self.expire_time = datetime.datetime.today()
        
        super(Feature, self).save(*args, **kwargs)
        
        return None
    
    def update(self, geometry=None, *args, **kwargs):
        """
        This function updates the feature if the new geometry
        is different from the saved one.
        
        Also if feature is updated it returns a new feature
        with the new geometry and sets expired time on the
        old one.
        """
        if(geometry != None and geometry != self.geometry):
            #set old feature as expired
            self.expire_time = datetime.datetime.today()
            super(Feature, self).save(*args, **kwargs)
        
            #save the new feature
            new_feature = Feature(user = self.user,
                                  geometry = geometry)
            new_feature.save()
            return new_feature
        
        return self   
        
    def geojson(self):
        """
        Returns a geojson object of with the latest properties
        belonging to this feature.
        """
        properties = None
        properties_dict = None
        
        try:
            # this should be changed to support different time queries
            properties = Property.objects.filter(feature__exact=self)\
                                            .latest('create_time')

            properties_dict = json.loads(properties.json_string)

        except ObjectDoesNotExist:
            properties_dict = {}
            
        feature_json = {}
        
        feature_json = {"id": self.id,
                        "geometry": json.loads(self.geometry.json),
                        "properties": properties_dict}
        
        return feature_json
    
    def __unicode__(self):
        feature_json = self.geojson()
        
        return str(feature_json)
        
        
    class Meta:
        permissions = (
            ("can_view_all", "Can view all features"),
            ("can_view_non_confidential",
            "Can view the non confidential features"),)
   
class Property(models.Model):
    """
    This model saves all the properties for the features,
    
    >>> u = User.objects.create_user('test-property','')
    >>> f = Feature(geometry = 'POINT(2 3)', user = u)
    >>> f.save()
    >>> p = Property(feature = f, json_string='{"some_prop": 140}')
    >>> p.save()
    >>> p.expire_time
    >>> type(p.create_time)
    <type 'datetime.datetime'>
    >>> p1 = p.update('{"some_prop": 140}') #should not update same json
    >>> p1.id == p.id
    True
    >>> p1 = p.update('{"some_prop": 141}') #should update different json
    >>> p1.id == p.id
    False
    >>> type(p.expire_time)
    <type 'datetime.datetime'>
    >>> type(p1.expire_time)
    <type 'NoneType'>
    >>> p1.delete()
    >>> type(p1.expire_time)
    <type 'datetime.datetime'>
    """
    feature = models.ForeignKey(Feature, related_name='properties')
    json_string = models.TextField()

    create_time = models.DateTimeField(auto_now_add=True, null=True)
    expire_time = models.DateTimeField(null=True)
    
    objects = models.Manager()
    
    if USE_MONGODB:
        mongodb_collection_name = 'feature_properties'
        mongodb = MongoDBManager(collection_name = mongodb_collection_name) #manager for querying json
    
    def save(self, *args, **kwargs):    
        #save this new property
        super(Property, self).save(*args, **kwargs)
        
        self.save_json_to_mongodb()
                    
                
    def save_json_to_mongodb(self):
        """
        This function saves the JSON to mongodb
        """
        #do nothing if USE_MONGODB False
        if USE_MONGODB:
            insert_json = json.loads(self.json_string)
            Property.mongodb.save(insert_json, self.id)
        
    def delete(self, *args, **kwargs):
        self.expire_time = datetime.datetime.today()

        super(Property, self).save(*args, **kwargs)
        
        return None
    
    def update(self, json_string, *args, **kwargs):
        if self.json_string != json_string:
            #set old feature as expired
            self.expire_time = datetime.datetime.today()
            super(Property, self).save(*args, **kwargs)
            
            #save the new property
            new_property = Property(feature = self.feature,
                                    json_string = json_string)
            new_property.save()
            
            return new_property
        
        return self
    
    def geojson(self):
        """
        Returns a geojson Feature with these(this) properties.
        """
        properties = json.loads(self.json_string)
        properties['user_id'] = self.feature.user.id
        
        feature_dict = {"id": self.feature.id,
                        "type": "Feature",
                        "geometry": json.loads(self.feature.geometry.json),
                        "properties": properties}
        
        return feature_dict
    
    
    def __unicode__(self):
        return self.json_string