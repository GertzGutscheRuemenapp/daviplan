from rest_framework import routers
from datentool_backend.user.views import UserViewSet
from datentool_backend.site.views import (SiteSettingViewSet,
                                          ProjectSettingViewSet,
                                          BaseDataSettingViewSet)
#  vector tiles
from rest_framework_mvt.views import mvt_view_factory
from django.conf.urls import url

from .population.models import RasterCell
from .area.views import (LayerGroupViewSet,
                         WMSLayerViewSet, SourceViewSet,
                         AreaLevelViewSet, AreaViewSet)

from .demand.views import (DemandRateSetViewSet, DemandRateViewSet,
                           ScenarioDemandRateViewSet)

from .indicators.views import (ModeViewSet, ModeVariantViewSet,
                               #ReachabilityMatrixViewSet,
                               RouterViewSet,
                               IndicatorViewSet)

from .infrastructure.views import (InfrastructureViewSet, FieldTypeViewSet,
                                   ServiceViewSet, PlaceViewSet,
                                   CapacityViewSet, PlaceFieldViewSet,
                                   FClassViewSet)
from .logging.views import (CapacityUploadLogViewSet, PlaceUploadLogViewSet,
                            AreaUploadLogViewSet)
from .population.views import (YearViewSet, RasterViewSet,
                               PopulationRasterViewSet, GenderViewSet,
                               AgeGroupViewSet,
                               DisaggPopRasterViewSet, PrognosisViewSet,
                               PrognosisEntryViewSet, PopulationViewSet,
                               PopulationEntryViewSet, PopStatisticViewSet,
                               PopStatEntryViewSet)
                               # ,RasterCellTileViewSet)
from .user.views import PlanningProcessViewSet, ScenarioViewSet
from datentool_backend.utils.routers import SingletonRouter

router = routers.SimpleRouter()
router.register(r'users', UserViewSet, basename='users')

# areas
router.register(r'layergroups', LayerGroupViewSet, basename='layergroups')
router.register(r'wmslayers', WMSLayerViewSet, basename='wmslayers')
router.register(r'sources', SourceViewSet, basename='sources')
router.register(r'arealevels', AreaLevelViewSet, basename='arealevels')
router.register(r'areas', AreaViewSet, basename='areas')

# demand
router.register(r'demandratesets', DemandRateSetViewSet,
                basename='demandratesets')
router.register(r'demandrates', DemandRateViewSet, basename='demandrates')
router.register(r'scenariodemandrates', ScenarioDemandRateViewSet,
                basename='scenariodemandrates')
# indicator
router.register(r'modes', ModeViewSet, basename='modes')
router.register(r'modevariants', ModeVariantViewSet, basename='modevariants')
#router.register(r'reachabilitymatrices', ReachabilityMatrixViewSet,
                #basename='reachabilitymatrices')
router.register(r'routers', RouterViewSet, basename='routers')
router.register(r'indicators', IndicatorViewSet, basename='indicators')

# infrastructure
router.register(r'infrastructures', InfrastructureViewSet,
                basename='infrastructures')
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
router.register(r'years', YearViewSet, basename='years')
router.register(r'rasters', RasterViewSet, basename='rasters')
router.register(r'populationrasters', PopulationRasterViewSet,
                basename='populationrasters')
router.register(r'gender', GenderViewSet, basename='gender')
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


#urlpatterns = [path("api/rastercells/", mvt_view_factory(RasterCell)), ]


#urlpatterns = [
    #path('rastercells', RasterCellTileViewSet, name="rastercells"),
#]

#urlpatterns = [
    #path('rastercells/<int:pk>/tile/<int:z>/<int:x>/<int:y>', RasterCellTileViewSet.as_view(), name="rastercells"),
#]

# users
router.register(r'planningprocesses', PlanningProcessViewSet, basename='planningprocesses')
router.register(r'scenarios', ScenarioViewSet, basename='scenarios')

# site
srouter = SingletonRouter()
srouter.register('projectsettings', ProjectSettingViewSet,
                 basename='projectsettings')
srouter.register('basedatasettings', BaseDataSettingViewSet,
                 basename='basedatasettings')
srouter.register('sitesettings', SiteSettingViewSet, basename='sitesettings')

urlpatterns = router.urls + srouter.urls
