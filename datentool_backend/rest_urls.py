from rest_framework import routers

from .site.views import (SiteSettingViewSet,
                         ProjectSettingViewSet,
                         BaseDataSettingViewSet,
                         MatrixStatisticsViewSet,
                         YearViewSet)

from .area.views import (LayerGroupViewSet,
                         WMSLayerViewSet,
                         AreaLevelViewSet,
                         AreaViewSet,
                         FieldTypeViewSet,
                         AreaFieldViewSet,
                         )

from .demand.views import (GenderViewSet,
                           AgeGroupViewSet,
                           DemandRateSetViewSet)

from .modes.views import (NetworkViewSet,
                          ModeVariantViewSet)

from .indicators.views import (RouterViewSet,
                               FixedIndicatorViewSet,
                               StopViewSet,
                               MatrixStopStopViewSet,
                               MatrixCellPlaceViewSet,
                               MatrixCellStopViewSet,
                               MatrixPlaceStopViewSet,
                               )

from .infrastructure.views import (InfrastructureViewSet,
                                   ServiceViewSet,
                                   )

from .places.views import (PlaceViewSet,
                           CapacityViewSet,
                           PlaceFieldViewSet,
                           PlanningProcessViewSet,
                           ScenarioViewSet,
                           )

from .logging.views import LogViewSet

from .population.views import (RasterViewSet,
                               RasterCellViewSet,
                               PopulationRasterViewSet,
                               PrognosisViewSet,
                               PopulationViewSet,
                               PopulationEntryViewSet,
                               PopStatisticViewSet,
                               PopStatEntryViewSet)

from .user.views import UserViewSet


class SingletonRouter(routers.SimpleRouter):
    routes = [
       routers.Route(
           url=r'^{prefix}/$',
           mapping={
               'get': 'retrieve',
               'put': 'update',
               'patch': 'partial_update'
               },
           name='{basename}-detail',
           initkwargs={'suffix': 'Detail'},
           detail=True
           )
    ]

router = routers.SimpleRouter()
router.register(r'users', UserViewSet, basename='users')

# areas
router.register(r'layergroups', LayerGroupViewSet, basename='layergroups')
router.register(r'wmslayers', WMSLayerViewSet, basename='wmslayers')
router.register(r'arealevels', AreaLevelViewSet, basename='arealevels')
router.register(r'areas', AreaViewSet, basename='areas')
router.register(r'areafields', AreaFieldViewSet, basename='areafields')

# demand
router.register(r'demandratesets', DemandRateSetViewSet,
                basename='demandratesets')

# indicator
router.register(r'networks', NetworkViewSet, basename='networks')
router.register(r'modevariants', ModeVariantViewSet, basename='modevariants')
router.register(r'stops', StopViewSet, basename='stops')
router.register(r'matrixstopstops', MatrixStopStopViewSet, basename='matrixstopstops')
router.register(r'matrixcellplaces', MatrixCellPlaceViewSet, basename='matrixcellplaces')
router.register(r'matrixcellstops', MatrixCellStopViewSet, basename='matrixcellstops')
router.register(r'matrixplacestops', MatrixPlaceStopViewSet, basename='matrixplacestops')
router.register(r'routers', RouterViewSet, basename='routers')
router.register(r'indicators', FixedIndicatorViewSet, basename='fixedindicators')

# infrastructure
router.register(r'scenarios', ScenarioViewSet, basename='scenarios')
router.register(r'places', PlaceViewSet, basename='places')
router.register(r'capacities', CapacityViewSet, basename='capacities')
router.register(r'fieldtypes', FieldTypeViewSet, basename='fieldtypes')
router.register(r'placefields', PlaceFieldViewSet, basename='placefields')

# logging
router.register(r'logs', LogViewSet, basename='logs')

# population
router.register(r'years', YearViewSet, basename='years')
router.register(r'rasters', RasterViewSet, basename='rasters')
router.register(r'rastercells', RasterCellViewSet, basename='rastercells')
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
router.register(r'planningprocesses', PlanningProcessViewSet,
                basename='planningprocesses')
router.register(r'infrastructures', InfrastructureViewSet,
                basename='infrastructures')
router.register(r'services', ServiceViewSet, basename='services')

# site
router.register('basedatasettings', BaseDataSettingViewSet,
                basename='basedatasettings')
router.register('matrixstatistics', MatrixStatisticsViewSet,
                basename='matrixstatistics')
srouter = SingletonRouter()
srouter.register('projectsettings', ProjectSettingViewSet,
                 basename='projectsettings')
srouter.register('sitesettings', SiteSettingViewSet, basename='sitesettings')

urlpatterns = router.urls + srouter.urls
