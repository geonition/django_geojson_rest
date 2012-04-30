# -*- coding: utf-8 -*-
from django.conf.urls.defaults import patterns
from django.conf.urls.defaults import url
from views import FeatureView
from views import PropertyView

urlpatterns = patterns('geojson_rest.views',

    url(r'^feat$',
        FeatureView.as_view(),
        {'user': '@me',
         'group': '@self'},
        name="feat"),

    (r'^feat/(?P<user>@?[-+_\w\.]+)$',
    FeatureView.as_view(),
    {'group': '@self'}),

    (r'^feat/(?P<user>@?[-+_\w\.]+)/(?P<group>@?[-+_\w]+)$',
    FeatureView.as_view()),

    (r'^feat/(?P<user>@?[-+_\w\.]+)/(?P<group>@?[-+_\w]+)/(?P<feature>@?\d+)$',
    FeatureView.as_view()),

    url(r'^prop$',
        PropertyView.as_view(),
        {'user': '@me',
         'group': '@self'},
        name="prop"),

    (r'^prop/(?P<user>@?[-+_\w\.]+)$',
    PropertyView.as_view(),
    {'group': '@self'}),

    (r'^prop/(?P<user>@?[-+_\w\.]+)/(?P<group>@?[-+_\w]+)$',
    PropertyView.as_view()),

    (r'^prop/(?P<user>@?[-+_\w\.]+)/(?P<group>@?[-+_\w]+)/(?P<feature>@?\d+|@null)$',
    PropertyView.as_view()),

    (r'^prop/(?P<user>@?[-+_\w\.]+)/(?P<group>@?[-+_\w]+)/(?P<feature>@?\d+|@null)/(?P<property>@?\d+)$',
    PropertyView.as_view()),

)
