from rest_framework import routers
from datentool_backend.user.views import UserViewSet
from datentool_backend.site.views import SiteSettingsViewSet
from .infrastructure.views import InfrastructureViewSet

router = routers.SimpleRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'settings', SiteSettingsViewSet, basename='settings')
router.register(r'infrastructure', InfrastructureViewSet, basename='infrastructure')

urlpatterns = router.urls