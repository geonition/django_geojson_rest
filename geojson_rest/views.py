from django.conf import settings
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.core.exceptions import ObjectDoesNotExist
from django.utils import simplejson as json
from geonition_utils.exceptions import Http400
from geonition_utils.http import HttpResponse
from geonition_utils.http import HttpResponseBadRequest
from geonition_utils.http import HttpResponseCreated
from geonition_utils.http import HttpResponseForbidden
from geonition_utils.http import HttpResponseNotFound
from geonition_utils.http import HttpResponseUnauthorized
from geonition_utils.views import RequestHandler
from geojson_rest.models import Feature
from geojson_rest.models import Property

class FeatureView(RequestHandler):

    def get(self,
            request,
            user = '@me',
            group = '@self',
            feature = None):
        
        #do not do anything if user has not created a session
        if not request.user.is_authenticated():
            return HttpResponseUnauthorized("The request has to be made by a"
                                            "signed in user")
        
#         # we need srid of the questionnaire map
#         # Check if we have maps application installed, if not use geometry column srid
#         try:
#             from maps.models import Map
#             # At the moment questionnaires always use map named questionnaire map.
#             # This should not be hardcoded.
#             # If named map is not found we use geometry column srid.
#             map_srid = int(Map.objects.get(slug_name = 'questionnaire-map').projection)
#             #take initial all transformed to map coordinates
#             features = Feature.objects.all().transform(map_srid)
#         except (ImportError, ObjectDoesNotExist):
#             #take initial all
#             features = Feature.objects.all()
            

        #take initial all
        features = Feature.objects.all()
        
        #filter the ones that has feature_id feature
        if feature != None:
            features = features.filter(id = feature)
        
        #filter the ones that belong to the group
        if group != '@all':
            features = features.filter(group = group)
        
        #filter the ones that belong to the user
        if user != '@all' and user != '@others':
            user_obj = get_user(request, username = user)
        
            if user != '@me':
            
                if request.user != user_obj:
                    features = features.filter(user = user_obj,
                                               private = False)
                else:
                    features = features.filter(user = user_obj)
                
            else:
                features = features.filter(user = user_obj)  
        
        elif user == '@others':
            features = features.filter(private = False)
            features = features.exclude(user = request.user)
            
        else: # user is @all
            if request.user and request.user.is_staff:
                pass
            else:
                own_features = features.filter(user = request.user)
                others_features = features.filter(private = False)
                others_features = others_features.exclude(user = request.user)
                features = own_features | others_features
                
        
        if len(features) > 0:
            srid = features[0].geometry.srid
        else:
            srid = getattr(settings, "SPATIAL_REFERENCE_SYSTEM_ID", 4326)
            
        featurecollection = {
            'type': 'FeatureCollection',
            'features': 'FEATURES',
            'crs': {"type": "name", "properties": {"code": "EPSG:%i" % srid}}
        }
        collection_str = json.dumps(featurecollection)
        collection_str = collection_str.replace(
                '\"FEATURES\"',
                '[' + ', '.join([feat.get_json_str() for feat in features]) + ']')
        return HttpResponse(collection_str)
        
    def post(self,
            request,
            user = '@me',
            group = '@self',
            feature = None):
        group = group[:50]
        
        # load the json and validate format
        json_object = json.loads(request.body)
        user = get_user(request,
                        username = user)
        
        if user == None:
            return HttpResponseBadRequest('You need to create a session before creating features')
        
        elif user != request.user:
            return HttpResponseForbidden('You cannot create featues for other users')
        
        json_obj_response = {}
        
        new_feature = Feature(user = user,
                              group = group)
        new_feature.create(json_object)
        uri = "%s/%s/%s/%i" % (reverse('feat'),
                               user.username,
                               group,
                               new_feature.id)
        created_entity = json.dumps(new_feature.to_json())
        
        return HttpResponseCreated(uri, created_entity)

    def put(self,
            request,
            user = '@me',
            group = '@self',
            feature = None):
        group = group[:50]
        
        if feature == None:
            return HttpResponseBadRequest('You need to provide a feature id')
        
        if request.user != get_user(request, user):
            return HttpResponseForbidden('You can only update your own features')
        
        update_feature = Feature.objects.get(id = feature)
        json_object = json.loads(request.body)
        update_feature.update(json_object, request.user)
            
        return HttpResponse(json.dumps(update_feature.to_json()))

    def delete(self,
               request,
               user = '@me',
               group = '@self',
               feature = None):
        
        if feature == None:
            return HttpResponseBadRequest('A feature id has to be given for delete')
        
        user = get_user(request, user)
        # only the user that 'owns' the feature can delete it
        if request.user == user and request.user.is_authenticated():
            Feature.objects.get(id = feature,
                                user = user).delete()
            return HttpResponse("A feature was deleted")
        
        else:
            return HttpResponseForbidden("You can only delete features that "
                                         "are owned by the currently registered user.")
            
    
class PropertyView(RequestHandler):
    
    def get(self,
            request,
            user = '@me',
            group = '@self',
            feature = None,
            property = None):
        
        properties = [] #default empty list
        
        #query the most restrictive first
        properties = Property.objects.filter(feature=None)
        if property != None and property != '@all':
            properties = properties.filter(id = property)
            
        if user == '@me' and request.user.is_authenticated():
            user = get_user(request, user)
            properties = properties.filter(user = user)
        elif user == '@me':
            return HttpResponseBadRequest("The user @me is not authenticated")
            
        if len(properties) == 0:
            return HttpResponseNotFound("The property you queried was not found")
        elif len(properties) == 1:
            return HttpResponse(json.dumps(properties[0].to_json()))
        else:
            property_collection = {
                'totalResults': len(properties),
                'entry': 'ENTRY'
            }
            collection_str = json.dumps(property_collection)
            collection_str = collection_str.replace(
                    '\"ENTRY\"',
                    '[' + ', '.join([prop.get_json_str() for prop in properties]) + ']')
            return HttpResponse(collection_str)
    
    def post(self,
            request,
            user = '@me',
            group = '@self',
            feature = '@null'):
        group = group[:50]
        
        # load the json and validate format
        json_object = json.loads(request.body)
        user = get_user(request,
                        username = user)
        if user == None:
            return HttpResponseBadRequest('You need to create a session before creating properties')
        elif user != request.user:
            return HttpResponseForbidden('You cannot create properties for other users')
        
        json_obj_response = {}
        new_property = Property(user = user,
                                group = group)
        new_property.create(json_object)
        
        uri = ""
        if feature != '@null': #connect feature to property
            Feature.objects.get(id = feature,
                               group = group).properties.add(new_property)
            uri = "%s/%s/%s/%s/%i" % (reverse('prop'),
                                      user.username,
                                      group,
                                      feature,
                                      new_property.id)
        else:
            uri = "%s/%s/%s/%s/%i" % (reverse('prop'),
                                      user.username,
                                      group,
                                      feature,
                                      new_property.id)
        
        created_entity = json.dumps(new_property.to_json())
        
        return HttpResponseCreated(uri, created_entity)
        
    def put(self,
            request,
            user = '@me',
            group = '@self',
            feature = None,
            property = None):
        group = group[:50]
        
        if property == None:
            return HttpResponseBadRequest("You need to provide a property id "
                                          "to make this request")
        else:
            json_object = json.loads(request.body)
            user = get_user(request, user)
            if user == request.user:
                property = Property.objects.get(id = property,
                                            user = user)
                property.update(json_object)
            else:
                return HttpResponseForbidden('You cannot update others properties')
        
        return HttpResponse(json.dumps(property.to_json()))
    
    def delete(self,
            request,
            user = '@me',
            group = '@self',
            feature = None,
            property = None):
        
        if property == None:
            return HttpResponseBadRequest('you need to provide a property id')
        elif not request.user.is_authenticated():
            return HttpResponseForbidden('You need to sign in to delete properties')
        else:
            Property.objects.get(id = property).delete()
        
        return HttpResponse("A property was deleted")

    
def get_user(request, username = '@me'):
        
    if username == '@me':
        user = request.user
    else:
        user = User.objects.get(username = username)
    
    return user
