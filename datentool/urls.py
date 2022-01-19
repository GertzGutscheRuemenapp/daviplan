"""datentool URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.conf.urls import url, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView
)

from datentool_backend.views import AreaLevelTileView

from .views import HomePageView

urlpatterns = [
    path('django-admin/', admin.site.urls),
    url('api/', include('datentool_backend.rest_urls')),
    path('api/token/', TokenObtainPairView.as_view(),
         name='token_obtain_pair'),
    path('api/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    path('api/token/refresh/', TokenRefreshView.as_view(),
         name='token_refresh'),
    path('tiles/arealevels/<int:pk>/tile/<int:z>/<int:x>/<int:y>/',
         AreaLevelTileView.as_view(), name="layer-tile"),
    # match all routes to the home page (entry point to angular) to let angular
    # handle the routing, /api and /static routes are still handled by django
    # automatically, for some reason /media is not, so it is excluded here
    url('^(?!media).*', HomePageView.as_view(), name='home'),
]
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
