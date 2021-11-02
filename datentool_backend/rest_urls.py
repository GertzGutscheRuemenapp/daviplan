from rest_framework import routers
from datentool_backend.user.views import UserViewSet
from datentool_backend.site.views import SiteSettingsViewSet

from .area.views import (SymbolFormViewSet, MapSymbolsViewSet, LayerGroupViewSet,
                         WMSLayerViewSet, InternalWFSLayerViewSet, SourceViewSet,
                         AreaLevelViewSet, AreaViewSet)

from .demand.views import (DemandRateSetViewSet, DemandRateViewSet)

from .infrastructure.views import InfrastructureViewSet

router = routers.SimpleRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'settings', SiteSettingsViewSet, basename='settings')

# areas
router.register(r'symbolform', SymbolFormViewSet, basename='symbolform')
router.register(r'mapsymbols', MapSymbolsViewSet, basename='mapsymbols')
router.register(r'layergroup', LayerGroupViewSet, basename='layergroup')
router.register(r'wmslayer', WMSLayerViewSet, basename='wmslayer')
router.register(r'internalwfslayer', InternalWFSLayerViewSet, basename='internalwfslayer')
router.register(r'source', SourceViewSet, basename='source')
router.register(r'arealevel', AreaLevelViewSet, basename='arealevel')
router.register(r'area', AreaViewSet, basename='area')

# demand
router.register(r'demandrateset', DemandRateSetViewSet, basename='demandrateset')
router.register(r'demandrate', DemandRateViewSet, basename='demandrate')

# infrastructure
router.register(r'infrastructure', InfrastructureViewSet, basename='infrastructure')



urlpatterns = router.urls