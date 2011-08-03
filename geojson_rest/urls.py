# -*- coding: utf-8 -*-
from django.conf.urls.defaults import patterns
from django.conf.urls.defaults import url

urlpatterns = patterns('geojson_rest.views',
                       
            #feature rest
            url(r'^',
                'feature',
                name="api_feature"),
              
        )
