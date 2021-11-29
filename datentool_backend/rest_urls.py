from rest_framework import routers
from datentool_backend.user.views import UserViewSet
from datentool_backend.site.views import SiteSettingsViewSet

from .area.views import (SymbolFormViewSet, MapSymbolsViewSet, LayerGroupViewSet,
                         WMSLayerViewSet, InternalWFSLayerViewSet, SourceViewSet,
                         AreaLevelViewSet, AreaViewSet)

from .demand.views import (DemandRateSetViewSet, DemandRateViewSet)

from .indicators.views import (ModeViewSet, ModeVariantViewSet,
                               ReachabilityMatrixViewSet, RouterViewSet,
                               IndicatorViewSet)

from .infrastructure.views import (InfrastructureViewSet, FieldTypeViewSet,
                                   QuotaViewSet, ServiceViewSet, PlaceViewSet,
                                   CapacityViewSet, PlaceFieldViewSet,
                                   FClassViewSet)
from .logging.views import (CapacityUploadLogViewSet, PlaceUploadLogViewSet,
                            AreaUploadLogViewSet)
from .population.views import (RasterViewSet, PopulationRasterViewSet, GenderViewSet,
                               AgeClassificationViewSet, AgeGroupViewSet,
                               DisaggPopRasterViewSet, PrognosisViewSet,
                               PrognosisEntryViewSet, PopulationViewSet,
                               PopulationEntryViewSet, PopStatisticViewSet,
                               PopStatEntryViewSet)
from .user.views import ProjectViewSet, ScenarioViewSet

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
router.register(r'reachabilitymatrices', ReachabilityMatrixViewSet,
                basename='reachabilitymatrices')
router.register(r'routers', RouterViewSet, basename='routers')
router.register(r'indicators', IndicatorViewSet, basename='indicators')

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

# logging
router.register(r'capacityuploadlogs', CapacityUploadLogViewSet,
                basename='capacityuploadlogs')
router.register(r'placeuploadlogs', PlaceUploadLogViewSet,
                basename='placeuploadlogs')
router.register(r'areauploadlogs', AreaUploadLogViewSet,
                basename='areauploadlogs')

# population
router.register(r'rasters', RasterViewSet, basename='rasters')
router.register(r'populationrasters', PopulationRasterViewSet,
                basename='populationrasters')
router.register(r'gender', GenderViewSet, basename='gender')
router.register(r'ageclassifications', AgeClassificationViewSet,
                basename='ageclassifications')
router.register(r'agegroups', AgeGroupViewSet, basename='agegroups')
router.register(r'disaggpoprasters', DisaggPopRasterViewSet,
                basename='disaggpoprasters')
router.register(r'prognoses', PrognosisViewSet,
                basename='prognoses')
router.register(r'prognosisentries', PrognosisEntryViewSet,
                basename='prognosisentries')
router.register(r'populations', PopulationViewSet,basename='populations')
router.register(r'populationentries', PopulationEntryViewSet,
                basename='populationentries')
router.register(r'popstatistics', PopStatisticViewSet, basename='popstatistics')
router.register(r'popstatentries', PopStatEntryViewSet, basename='popstatentries')

# users
router.register(r'projects', ProjectViewSet, basename='projects')
router.register(r'scenarios', ScenarioViewSet, basename='scenarios')


urlpatterns = router.urls
