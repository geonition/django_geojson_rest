# -*- coding: utf-8 -*-
from django.conf.urls.defaults import patterns
from django.conf.urls.defaults import url
from views import FeatureView

urlpatterns = patterns('geojson_rest.views',

                url(r'^feat$',
                    FeatureView.as_view(),
                    {'user': '@me',
                     'group': '@self'},
                    name="feat"),

                (r'^feat/(?P<user>@?[-+_\w]+)$',
                FeatureView.as_view(),
                {'group': '@self'}),

                (r'^feat/(?P<user>@?[-+_\w]+)/(?P<group>@?[-+_\w]+)$',
                FeatureView.as_view()),

                (r'^feat/(?P<user>@?[-+_\w]+)/(?P<group>@?[-+_\w]+)/(?P<feature>@?\d+)$',
                FeatureView.as_view()),

        )
