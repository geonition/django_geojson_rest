from django.http import HttpResponse
from django.http import HttpResponseForbidden
from django.http import HttpResponseBadRequest
from django.http import HttpResponseNotFound
from django.core.exceptions import ObjectDoesNotExist
from django.utils import translation
from django.utils.encoding import smart_unicode
from django.contrib.gis.gdal import OGRGeometry
from django.contrib.gis.geos.error import GEOSException
from softgis_feature.models import Feature
from softgis_feature.models import Property
from HttpResponseExtenders import HttpResponseNotAuthorized
from django.contrib.gis.gdal.error import OGRException
from Commons import CustomError, SoftGISFormatUtils

import settings
import urllib2
import logging
import sys
import datetime

if sys.version_info >= (2, 6):
    import json
else:
    import simplejson as json

_ = translation.ugettext
logger = logging.getLogger('api.feature.view')

USE_MONGODB = getattr(settings, "USE_MONGODB", False)
SEPARATOR = getattr(settings, "SEPARATOR_FOR_CSV_FILE", ";")

#Views for the geometry API
def feature(request):
    """
    This function handles the feature part of the softgis REST api
    
    On GET request this function returns a geojson featurecollection
    matching the query string.
    
    On POST request this function adds a new feature to the database.
    
    On PUT request this function will update a feature that has
    a given id.
    
    On DELETE request this function removes existing feature/feature collection from 
    the database.
    """
    
    
  
    def save_feature(feature_json):
        geometry = None
        properties = None
        
        try:
            geometry = feature_json['geometry']
            properties = feature_json['properties']
        except KeyError, keyError:
            logger.warning("The geojson type Feature does not include the required properties and geometry")	
            raise keyError            

        
        
        #geos = GEOSGeometry(json.dumps(geometry))
        # Have to make OGRGeometry as GEOSGeometry
        # does not support spatial reference systems
        try:
            
            geos = OGRGeometry(json.dumps(geometry)).geos
        except OGRException, ogrException:            
            logger.warning("The submited geometry is invalid: %s " % ogrException)	
            raise ogrException
        except GEOSException, geosEx:
            logger.warning("Error encountered checking Geometry: %s " % geosEx)
            raise geosEx

        #save the feature
        new_feature = Feature(geometry=geos,
                            user=request.user)
        new_feature.save()
        

        #add the id to the feature json
        identifier = new_feature.id
        logger.info("The feature was successfully saved with id %i" %identifier)

        feature_json['id'] = identifier
        
        #save the properties of the new feature
        new_property = Property(feature=new_feature,
                                json_string=json.dumps(properties))
        new_property.save()
        logger.info("The property was successfuly saved")

        return identifier

    def update_feature(feature_json):
        geometry = None
        properties = None
        feature_id = None
        
        try:
            geometry = feature_json['geometry']
            properties = feature_json['properties']
            feature_id = feature_json['id']
        except KeyError, keyError:
            logger.debug("The geojson type Feature does not include the required properties, geometry and id for updating")	
            raise keyError
         
        #get the feature to be updated
        feature_old = None
        try:
            feature_old = Feature.objects.get(id__exact = feature_id)
        except DoesNotExist, doesNotExist:
            logger.debug("The Feature with id %i was not found" %feature_id)
            raise CustomError("The feature with id %i was not found. Details %s" % (feature_id, str(doesNotExist)), 400, str(doesNotExist))
            
        
        if feature_old.user != request.user:
            logger.debug("The Feature with id %i was not found was added by user %s and it can not be modified by current user %s" %(feature_id, feature_old.user.username, request.user.username))
            raise CustomError( "You do not have permission to update feature %i" % feature_id, 403)
        
        
        #geos = GEOSGeometry(json.dumps(geometry))
        # Have to make OGRGeometry as GEOSGeometry
        # does not support spatial reference systems
        try:
            
            geos = OGRGeometry(json.dumps(geometry)).geos
        except OGRException, ogrException:            
            logger.warning("The submited geometry is invalid: %s " % ogrException)
            raise CustomError("The submited geometry is invalid: %s " % ogrException, 400, str(ogrException))
        except GEOSException, geosEx:
            logger.warning("Error encountered checking Geometry: %s " % geosEx)
            raise geosEx    
        
        feature = feature_old.update(geometry = geos)
        logger.info("The Feature %i was updated successfully" % feature_id)            

        #save the properties of the new feature
        cur_property = Property.objects\
                        .filter(feature = feature_old)\
                        .latest('create_time')
        
        if feature_old.id == feature.id: #if there was nothing updated
            new_property = cur_property.update(json.dumps(properties))
        else: #feature was updated so new property created
            cur_property.delete()
            new_property = Property(feature=feature,
                                json_string=json.dumps(properties))
            new_property.save()
        
        return feature_id        

    if request.method  == "GET":
        
        if not request.user.is_authenticated():
            logger.warning("There was a %s request to features but the user was not authenticated" % request.method)
            return HttpResponseNotAuthorized(_("You need to login or create a session in order to query features"))  
        
        # get the definied limiting parameters
        limiting_param = request.GET.items()
        
        feature_collection = {"type":"FeatureCollection", "features": []}
        
        feature_queryset = None

        #filter according to permissions
        if(request.user.has_perm('softgis_api.can_view_all')):
            feature_queryset = Feature.objects.all()

        elif(request.user.is_authenticated()):
            #else the user can only view his/her own features
            feature_queryset = \
                    Feature.objects.filter(user__exact = request.user)
        else:
            feature_queryset = Feature.objects.none()

        logger.debug("GET request to features() from user %s and with params %s" % (request.user.username, limiting_param))

        property_queryset = Property.objects.all()
        mongo_query = {}

        format = "geojson"
        csv_header = []

        #filter according to limiting_params
        for key, value in limiting_param:
            
            key = str(key)

            # get the export format
            if key == "format":
                format = str(value)
                continue

            if key == "csv_header":
                try:
                    csv_header = json.loads(value)
                except ValueError, exc:
                    message = 'JSON decode error: %s' % unicode(exc)
                    logger.warning(message)
                    return HttpResponseBadRequest(message)
                continue

            if value.isnumeric():
                value = int(value)
            elif value == "true":
                value = True
            elif value == "false":
                value = False
                
            key_split = key.split('__')
            command = ""
            
            if len(key_split) > 1:
                key = key_split[0]
                command = key_split[1]
            
            if(key == "user_id"):
                feature_queryset = feature_queryset.filter(user__exact = value)
                
            elif(key == "id"):
                feature_queryset = feature_queryset.filter(id__exact = value)
            
            elif(key == "time"):
                
                dt = None
                 
                if(command == "now" and value):
                    dt = datetime.datetime.now()
                elif(command == "now" and not value):
                    continue
                else:
                    dt = SoftGISFormatUtils.parse_time(value)
                
                property_qs_expired = property_queryset.filter(create_time__lte = dt)
                property_qs_expired = property_qs_expired.filter(expire_time__gte = dt)
                    
                property_qs_not_exp = property_queryset.filter(create_time__lte = dt)
                property_qs_not_exp = property_qs_not_exp.filter(expire_time = None)
                property_qs_not_exp = property_qs_not_exp.exclude(id__in = property_qs_expired)
                    
                property_queryset = property_qs_not_exp | property_qs_expired
                    
                #do the same for features
                feature_ids = property_queryset.values_list('feature_id', )
                feature_queryset = feature_queryset.filter(id__in = feature_ids)
                feature_qs_expired = feature_queryset.filter(expire_time__gt = dt)
                feature_qs_expired = feature_qs_expired.filter(create_time__lt = dt)
                feature_qs_not_expired = feature_queryset.filter(expire_time = None)
                feature_queryset = feature_qs_not_expired | feature_qs_expired 
                
            #mongodb queries should be built here
            elif USE_MONGODB:
                
                if command == "max":

                    if mongo_query.has_key(key):
                        mongo_query[key]["$lte"] = value
                    else:
                        mongo_query[key] = {}
                        mongo_query[key]["$lte"] = value
                        
                elif command == "min":

                    if mongo_query.has_key(key):
                        mongo_query[key]["$gte"] = value
                    else:
                        mongo_query[key] = {}
                        mongo_query[key]["$gte"] = value

                elif command == "":
                    mongo_query[key] = value
        
                
        #filter the queries acccording to the json
        if len(mongo_query) > 0:
            mongo_query['_id'] = {"$in": list(property_queryset.values_list('id', flat=True))}
            qs = Property.mongodb.find(mongo_query)
            property_queryset = property_queryset.filter(id__in = qs.values_list('id', flat=True))
        
        #filter the properties not belonging to feature_queryset
        property_queryset = property_queryset.filter(feature__in = feature_queryset)
        
        #if output format is csv prepare the file header
        csv_string = ""

        if format == "csv":
            for i, key in enumerate(csv_header):
                #check index and put separator
                if i > 0:
                    csv_string += SEPARATOR
                csv_string += key 


        for prop in property_queryset:
            if format == "geojson":
                feature_collection['features'].append(prop.geojson())
            elif format == "csv":
                csv_string += '\n'
                #insert value for that property
                j=0
                for j, key in enumerate(csv_header):
                    if j > 0:
                        csv_string += SEPARATOR
                    if key == "user_id":
                        csv_string += "%s" % prop.feature.user.id
                    elif key == "Geometry_WKT":
                        csv_string += "%s" % str(prop.feature.geometry.wkt)
                    elif key == "Geometry_geojson":
                        csv_string += "%s" % str(prop.feature.geometry.json)
                    else:
                        try:
                            properties = json.loads(prop.json_string)
                        except ValueError, exc:
                            message = 'JSON decode error: %s' % unicode(exc)
                            logger.warning(message)
                            return HttpResponseBadRequest(message)
                        try:
                            csv_string += str(properties[key]).replace(SEPARATOR, ' ')
                        except KeyError:
                            csv_string += ""
            else:
                logger.warning("The format requested %s is not supported" % format)
                return HttpResponseBadRequest(_("Data output format is not supported"))

        # According to GeoJSON specification crs member
        # should be on the top-level GeoJSON object
        # get srid from the first feature in the collection
        if property_queryset.exists():
            srid = property_queryset[0].feature.geometry.srid
        else:
            srid = getattr(settings, "SPATIAL_REFERENCE_SYSTEM_ID", 4326)

        crs_object =  {"type": "EPSG", "properties": {"code": srid}}
        
        # If the coordinate system is wgs84(4326) don't include 'crs'
        # see geojson specifications
        if srid != 4326 :
            feature_collection['crs'] = crs_object
        
        logger.debug("Returned feature collection %s" % feature_collection)  

        if format == "geojson":
            return HttpResponse(json.dumps(feature_collection),
                                mimetype="application/json")
        elif format == "csv":
            return HttpResponse(csv_string, mimetype="text/csv")
        else:
            return HttpResponseBadRequest(_("Data output format is not supported"))


    elif request.method == "POST":
        
        if not request.user.is_authenticated():
            logger.warning("There was a %s request to features but the user was not authenticated" % request.method)
            return HttpResponseNotAuthorized(_("You need to login or create a session in order to create features"))    

        #supports saving geojson Features
        feature_json = None
        
        try:
            logger.debug("POST request to features() with params %s " % request.POST.keys()[0])
            feature_json = json.loads(request.POST.keys()[0])
        except IndexError:
            return HttpResponseBadRequest(_("POST data was empty so could not create the feature"))
        except ValueError, exc:
            message = 'JSON decode error: %s' % unicode(exc)
            logger.warning(message)
            return HttpResponseBadRequest(message)
            
            
        geojson_type = None
        
        try:
            geojson_type = feature_json['type']
        except KeyError:
            logger.warning("The geojson does not include a type")	
            return HttpResponseBadRequest(_("geojson did not inclue a type." + \
                                          " Accepted types are " + \
                                          "'FeatureCollection' and 'Feature'."))
            


        #inner function to save one feature
        if geojson_type == "Feature":
            
            try:
                identifier = save_feature(feature_json)
                feature_json['id'] = identifier
            except KeyError:
                return HttpResponseBadRequest("geojson type 'Feature' " + \
                                        "requires properties "  + \
                                        "and geometry")
            except OGRException, ogrException:
                return HttpResponseBadRequest("The submited geometry is invalid")
            except GEOSException, geosEx:
                return HttpResponseBadRequest("Error encountered checking Geometry")
                

            return HttpResponse(json.dumps(feature_json))         

        elif geojson_type == "FeatureCollection":
            features = feature_json['features']
            ret_featurecollection = {
                "type": "FeatureCollection",
                "features": []
            }
            
            for feat in features:

                try:
                    identifier = save_feature(feat)
                    feat['id'] = identifier
                except KeyError:
                    return HttpResponseBadRequest("geojson type 'Feature' " + \
                                            "requires properties "  + \
                                            "and geometry")
                except OGRException, ogrException:
                    return HttpResponseBadRequest("The submited geometry is invalid: %s" % ogrException)
                except GEOSException, geosEx:
                    return HttpResponseBadRequest("Error encountered checking Geometry")
                
            ret_featurecollection['features'].append(feat)

            logger.info("The feature collection was successfuly saved")

            return HttpResponse(json.dumps(ret_featurecollection))
            
    elif request.method == "PUT":
        
        if not request.user.is_authenticated():
            return HttpResponseNotAuthorized(_("You need to login or create a session in order to update features"))    
        
        try:
            #supports updating geojson Features
            feature_json = json.loads(urllib2.unquote(request.raw_post_data.encode('utf-8')).decode('utf-8'))
        except ValueError, exc:
            message = 'JSON decode error: %s' % unicode(exc)
            logger.warning(message)
            return HttpResponseBadRequest(message)

        
        logger.debug("A PUT request was sent to features with params %s" % feature_json)

        try:
            geojson_type = feature_json['type']
        except KeyError:
            logger.debug("The geojson does not include a type")
            return HttpResponseBadRequest(_("geojson did not include a type." + \
                                          " Accepted types are " + \
                                          "'FeatureCollection' and 'Feature'."))

        if geojson_type == "Feature":
            try:
                feature_id = update_feature(feature_json)
            except keyError:
                return HttpResponseBadRequest("geojson feature requires " + \
                                        "properties, "  + \
                                        "geometry " + \
                                        "and id for updating")
            except GEOSException, geosEx:
                return HttpResponseBadRequest("Error encountered checking Geometry")    
            except CustomError, err:
                return HttpResponse(content = err.customMessage, status = err.statusCode)
                
                
            
            return HttpResponse(_(u"Feature with id %s was updated" % feature_id))
    
        elif geojson_type == "FeatureCollection":
                
            features = feature_json['features']
            
            for feat in features:  
                try:
                    feature_id = update_feature(feat)
                except keyError:
                    return HttpResponseBadRequest("geojson feature requires " + \
                                            "properties, "  + \
                                            "geometry " + \
                                            "and id for updating")
                except GEOSException, geosEx:
                    return HttpResponseBadRequest("Error encountered checking Geometry")    
                except CustomError, err:
                    return HttpResponse(content = err.customMessage, status = err.statusCode)

            
            return HttpResponse(_(u"Features updated"))
                    
    elif request.method  == "DELETE":
        """
        Get the array with the feature ids for delete
        """
        if not request.user.is_authenticated():
            return HttpResponseNotAuthorized(_("You need to login or create a session in order to delete features"))
            
        try:
            feature_ids = json.loads(request.GET.get("ids","[]"))
        except ValueError, exc:
            message = 'JSON decode error: %s' % unicode(exc)
            logger.warning(message)
            return HttpResponseBadRequest(message)
        
        logger.debug("A DELETE request was sent to features with the params %s" % feature_ids)

        if len(feature_ids) == 0:
            logger.warning("No feature id was provided to be deleted")
            return HttpResponseNotFound(_(u"You have to provide id of features to delete."))

        feature_queryset = Feature.objects.filter(id__in = feature_ids,
                                                user__exact = request.user)

            
        #set as expired
        exp_time = datetime.datetime.today()
        deleted_features = []
        for feat in feature_queryset:
            if(feat.expire_time == None):
                feat.expire_time = exp_time
                feat.save()
                deleted_features.append(feat.id)
                
        """
        Test if there were features already deleted (with an expiration time already set)
        and return not found
        """
        not_deleted = [id for id in feature_ids if id not in deleted_features]
        if len(not_deleted) > 0:
            logger.warning("Delete result: Features %s not found and featured %s deleted" % (not_deleted, deleted_features))
            return HttpResponseNotFound(_(u"Features %(not_deleted)s not found and featured %(deleted_features)s deleted." % {'not_deleted' : not_deleted, 'deleted_features' : deleted_features}))
        
        logger.info("All Features were deleted successfully")
        return HttpResponse(_(u"Features with ids %s deleted." % deleted_features))



