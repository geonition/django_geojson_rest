# -*- coding: utf-8 -*-
from django.conf.urls.defaults import patterns
from django.conf.urls.defaults import url
from views import Feature

urlpatterns = patterns('geojson_rest.views',

                url(r'^feat$',
                    Feature.as_view(),
                    {'user': '@me',
                     'group': '@self'},
                    name="feat"),

                (r'^feat/(?P<user>@?[-+_\w]+)$',
                Feature.as_view(),
                {'group': '@self'}),

                (r'^feat/(?P<user>@?[-+_\w]+)/(?P<group>@?\w+)$',
                Feature.as_view()),

                (r'^feat/(?P<user>@?[-+_\w]+)/(?P<group>@?\w+)/(?P<feature>@?\d+)$',
                Feature.as_view()),

        )
