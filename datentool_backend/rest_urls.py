from rest_framework import routers
from datentool_backend.user.views import UserViewSet
from datentool_backend.site.views import (SiteSettingViewSet,
                                          ProjectSettingViewSet,
                                          BaseDataSettingViewSet)

from .area.views import (LayerGroupViewSet, WMSLayerViewSet,
                         AreaLevelViewSet, AreaViewSet,
                         FieldTypeViewSet, FClassViewSet,
                         )

from .demand.views import (GenderViewSet,
                           AgeGroupViewSet,
                           DemandRateSetViewSet,
                           DemandRateViewSet,
                           )

from .modes.views import (ModeViewSet, ModeVariantViewSet,)
from .indicators.views import (RouterViewSet,
                               FixedIndicatorViewSet,
                               )

from .infrastructure.views import (ScenarioViewSet,
                                   PlaceViewSet,
                                   CapacityViewSet,
                                   PlaceFieldViewSet,
                                   )
from .logging.views import (CapacityUploadLogViewSet,
                            PlaceUploadLogViewSet,
                            AreaUploadLogViewSet)
from .population.views import (RasterViewSet,
                               PopulationRasterViewSet,
                               PrognosisViewSet,
                               PopulationViewSet,
                               PopulationEntryViewSet,
                               PopStatisticViewSet,
                               PopStatEntryViewSet)

from .user.views import (PlanningProcessViewSet,
                         YearViewSet,
                         InfrastructureViewSet,
                         ServiceViewSet, )
from datentool_backend.utils.routers import SingletonRouter

router = routers.SimpleRouter()
router.register(r'users', UserViewSet, basename='users')

# areas
router.register(r'layergroups', LayerGroupViewSet, basename='layergroups')
router.register(r'wmslayers', WMSLayerViewSet, basename='wmslayers')
router.register(r'arealevels', AreaLevelViewSet, basename='arealevels')
router.register(r'areas', AreaViewSet, basename='areas')

# demand
router.register(r'demandratesets', DemandRateSetViewSet,
                basename='demandratesets')
router.register(r'demandrates', DemandRateViewSet, basename='demandrates')

# indicator
router.register(r'modes', ModeViewSet, basename='modes')
router.register(r'modevariants', ModeVariantViewSet, basename='modevariants')
#router.register(r'reachabilitymatrices', ReachabilityMatrixViewSet,
                #basename='reachabilitymatrices')
router.register(r'routers', RouterViewSet, basename='routers')
router.register(r'indicators', FixedIndicatorViewSet, basename='areaindicators')

# infrastructure
router.register(r'scenarios', ScenarioViewSet, basename='scenarios')
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
router.register(r'years', YearViewSet, basename='years')
router.register(r'rasters', RasterViewSet, basename='rasters')
router.register(r'populationrasters', PopulationRasterViewSet,
                basename='populationrasters')
router.register(r'genders', GenderViewSet, basename='gender')
router.register(r'agegroups', AgeGroupViewSet, basename='agegroups')

router.register(r'prognoses', PrognosisViewSet,
                basename='prognoses')
router.register(r'populations', PopulationViewSet,basename='populations')
router.register(r'populationentries', PopulationEntryViewSet,
                basename='populationentries')
router.register(r'popstatistics', PopStatisticViewSet, basename='popstatistics')
router.register(r'popstatentries', PopStatEntryViewSet, basename='popstatentries')

# users
router.register(r'planningprocesses', PlanningProcessViewSet, basename='planningprocesses')
router.register(r'infrastructures', InfrastructureViewSet,
                basename='infrastructures')
router.register(r'services', ServiceViewSet, basename='services')

# site
srouter = SingletonRouter()
srouter.register('projectsettings', ProjectSettingViewSet,
                 basename='projectsettings')
srouter.register('basedatasettings', BaseDataSettingViewSet,
                 basename='basedatasettings')
srouter.register('sitesettings', SiteSettingViewSet, basename='sitesettings')

urlpatterns = router.urls + srouter.urls
