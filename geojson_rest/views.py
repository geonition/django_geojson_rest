from geonition_utils.views import RequestHandler
from django.http import HttpResponse

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
