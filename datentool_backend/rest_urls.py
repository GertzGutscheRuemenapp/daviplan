from rest_framework import routers
from datentool_backend.user.views import UserViewSet
from datentool_backend.site.views import SiteSettingsViewSet

router = routers.SimpleRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'settings', SiteSettingsViewSet, basename='settings')

urlpatterns = router.urls