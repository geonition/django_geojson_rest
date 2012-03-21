# -*- coding: utf-8 -*-
from django.conf.urls.defaults import patterns
from django.conf.urls.defaults import url
from views import Geo

urlpatterns = patterns('geojson_rest.views',

                url(r'^geo$',
                   Geo.as_view(),
                   {'user': '@me',
                    'group': '@self'},
                    name="geo"),

                (r'^geo/(?P<user>@?[-+_\w]+)$',
                Geo.as_view(),
                {'group': '@self'}),

                (r'^people/(?P<user>@?[-+_\w]+)/(?P<group>@?\w+)$',
                Geo.as_view()),

                (r'^people/(?P<user>@?[-+_\w]+)/(?P<group>@?\w+)/(?P<feature>@?\d+)$',
                Geo.as_view()),

        )
