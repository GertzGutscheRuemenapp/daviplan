from rest_framework import routers
from datentool_backend.user.views import UserViewSet
from datentool_backend.site.views import SiteSettingsViewSet

from .area.views import SymbolFormViewSet, MapSymbolsViewSet

from .infrastructure.views import InfrastructureViewSet

router = routers.SimpleRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'settings', SiteSettingsViewSet, basename='settings')

# areas
router.register(r'symbolform', SymbolFormViewSet, basename='symbolform')
router.register(r'mapsymbols', MapSymbolsViewSet, basename='mapsymbols')


# infrastructure
router.register(r'infrastructure', InfrastructureViewSet, basename='infrastructure')

urlpatterns = router.urls