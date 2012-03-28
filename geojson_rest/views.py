from django.conf import settings
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.utils import simplejson as json
from geonition_utils.exceptions import Http400
from geonition_utils.http import HttpResponse
from geonition_utils.http import HttpResponseCreated
from geonition_utils.http import HttpResponseBadRequest
from geonition_utils.views import RequestHandler
from models import Feature

class FeatureView(RequestHandler):

    def get(self,
            request,
            user = '@me',
            group = '@self',
            feature = None):
        
        print user
        print group
        print feature
        if feature != None:
            features = Feature.objects.filter(id = feature)
            
        elif user != '@all' and group != '@all':
            user = self.get_user(request, username = user)
            print user
            if user == request.user:
                features = Feature.objects.filter(user = user,
                                                  group = group)
                print features
            else:
                own_features = Feature.objects.filter(user = request.user,
                                                      group = group)
                others_features = Feature.objects.filter(user = user,
                                                         group = group,
                                                         private = False)
                features = own_features | others_features
                
        elif user == '@all' and group != '@all':
            features = Feature.objects.filter(group = group,
                                             private = False)
        elif user != '@all' and group == '@all':
            user = self.get_user(request, username = user)
            if user == request.user:
                features = Feature.objects.filter(user = user)
            else:
                features = Feature.objects.filter(user = user,
                                                 private = False)
        else:
            features = Feature.objects.filter(private = False)
            
        
        if len(features) > 0:
            srid = features[0].geometry.srid
        else:
            srid = getattr(settings, "SPATIAL_REFERENCE_SYSTEM_ID", 4326)
        
        featurecollection = {
            'type': 'FeatureCollection',
            'features': [feat.to_json() for feat in features],
            'crs': {"type": "EPSG", "properties": {"code": srid}}
        }
        return HttpResponse(json.dumps(featurecollection))
        
    def post(self,
            request,
            user = '@me',
            group = '@self',
            feature = None):
        
        # load the json and validate format
        json_object = json.loads(request.body)
        user = self.get_user(request,
                             username = user)
        
        if user == None:
            return HttpResponseBadRequest('You need to create a session before creating features')
        elif user != request.user:
            return HttpResponseBadRequest('You cannot create featues for other users')
        
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
        
        if feature == None:
            return HttpResponseBadRequest('You need to provide a feature id')
        
        if request.user != self.get_user(request, user):
            return HttpResponseBadRequest('You can only update your own features')
        
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
        
        Feature.objects.get(id = feature).delete()
        
        return HttpResponse("A feature was deleted")

    def get_user(self, request, username = '@me'):
        
        if username == '@me':
            user = request.user
        else:
            user = User.objects.get(username = username)
        
        return user