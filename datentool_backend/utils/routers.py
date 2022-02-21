from collections import OrderedDict

from django.urls import NoReverseMatch
from rest_framework import routers, views, reverse, response


class SingletonRouter(routers.SimpleRouter):
    routes = [
       routers.Route(
           url=r'^{prefix}/$',
           mapping={
               'get': 'retrieve',
               'put': 'update',
               'patch': 'partial_update'
               },
           name='{basename}-detail',
           initkwargs={'suffix': 'Detail'},
           detail=True
           )
    ]
