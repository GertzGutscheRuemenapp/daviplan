from rest_framework import routers
from datentool_backend.user.views import UserViewSet
from datentool_backend.site.views import SiteSettingsViewSet

from .area.views import (SymbolFormViewSet, MapSymbolsViewSet, LayerGroupViewSet,
                         WMSLayerViewSet, InternalWFSLayerViewSet, SourceViewSet,
                         AreaLevelViewSet, AreaViewSet)

from .demand.views import (DemandRateSetViewSet, DemandRateViewSet)

from .indicators.views import (ModeViewSet, ModeVariantViewSet)

from .infrastructure.views import (InfrastructureViewSet, FieldTypeViewSet,
                                   QuotaViewSet, ServiceViewSet, PlaceViewSet,
                                   CapacityViewSet, PlaceFieldViewSet,
                                   FClassViewSet)

router = routers.SimpleRouter()
router.register(r'users', UserViewSet, basename='users')
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
router.register(r'modevariants', ModeVariantViewSet, basename='modevariants')

# infrastructure
router.register(r'infrastructures', InfrastructureViewSet,
                basename='infrastructures')
router.register(r'quotas', QuotaViewSet, basename='quotas')
router.register(r'services', ServiceViewSet, basename='services')
router.register(r'places', PlaceViewSet, basename='places')
router.register(r'capacities', CapacityViewSet, basename='capacities')
router.register(r'fieldtypes', FieldTypeViewSet, basename='fieldtypes')
router.register(r'fclasses', FClassViewSet, basename='fclasses')
router.register(r'placefields', PlaceFieldViewSet, basename='placefields')

urlpatterns = router.urls
