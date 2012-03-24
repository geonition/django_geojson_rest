from geonition_utils.views import RequestHandler
from geonition_utils.http import HttpResponse
from models import Feature
from django.utils import simplejson as json

class Feature(RequestHandler):

    def get(self,
            request,
            user = '@me',
            group = '@self',
            feature = None):
        
        return HttpResponse("{}",
                            content_type = "application/json")
        
    def post(self,
            request,
            user = '@me',
            group = '@self',
            feature = None):
        
        print "post"
        print request
        print user
        print group
        print feature
        print request.body
        
        #validate the sent feature or featurecollection
        try:
            json_object = json.loads(request.body)
        except ValueError:
            return HttpBadRequest()
        geometry = json_object['geometry']
        properties = json_object['properties']
            
        return HttpResponse("{}",
                            content_type = "application/json")

    def put(self,
            request,
            user = '@me',
            group = '@self',
            feature = None):
        return HttpResponse("{}",
                            content_type = "application/json")

    def delete(self,
               request,
               user = '@me',
               group = '@self',
               feature = None):
        return HttpResponse("{}",
                            content_type = "application/json")
