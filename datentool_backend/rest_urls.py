from rest_framework import routers
from datentool_backend.user.views import UserViewSet
from datentool_backend.site.views import SiteSettingsViewSet

from .area.views import (SymbolFormViewSet, MapSymbolsViewSet, LayerGroupViewSet,
                         WMSLayerViewSet, InternalWFSLayerViewSet, SourceViewSet,
                         AreaLevelViewSet, AreaViewSet)

from .demand.views import (DemandRateSetViewSet, DemandRateViewSet)

from .indicators.views import (ModeViewSet)

from .infrastructure.views import InfrastructureViewSet

router = routers.SimpleRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'settings', SiteSettingsViewSet, basename='settings')

# areas
router.register(r'symbolforms', SymbolFormViewSet, basename='symbolforms')
router.register(r'mapsymbols', MapSymbolsViewSet, basename='mapsymbols')
router.register(r'layergroups', LayerGroupViewSet, basename='layergroups')
router.register(r'wmslayers', WMSLayerViewSet, basename='wmslayers')
router.register(r'internalwfslayers', InternalWFSLayerViewSet,
                basename='internalwfslayers')
router.register(r'sources', SourceViewSet, basename='sources')
router.register(r'arealevels', AreaLevelViewSet, basename='arealevels')
router.register(r'areas', AreaViewSet, basename='areas')

# demand
router.register(r'demandratesets', DemandRateSetViewSet,
                basename='demandratesets')
router.register(r'demandrates', DemandRateViewSet, basename='demandrates')

# indicator
router.register(r'modes', ModeViewSet, basename='modes')
router.register(r'modes', DemandRateViewSet, basename='modes')

# infrastructure
router.register(r'infrastructures', InfrastructureViewSet,
                basename='infrastructures')



urlpatterns = router.urls
