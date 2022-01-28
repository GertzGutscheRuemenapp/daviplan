from django.contrib.gis.geos import Point, Polygon, MultiPolygon

from datentool_backend.area.factories import AreaLevelFactory, AreaFactory, Area
from datentool_backend.user.factories import (InfrastructureFactory,
                                              Infrastructure,
                                              ServiceFactory,
                                              PlanningProcess)
from datentool_backend.infrastructure.factories import (ScenarioFactory,
                                                        PlaceFactory,
                                                        ServiceFactory,
                                                        CapacityFactory)

from datentool_backend.user.models import Year
from datentool_backend.demand.models import (Gender,
                                             AgeGroup,
                                             )
from datentool_backend.population.factories import (DisaggPopRasterFactory,
                                                    RasterCellFactory,
                                                    RasterCellPopulationFactory,
                                                    PopulationFactory,
                                                    )
from datentool_backend.population.models import (PopulationRaster,
                                                Raster,
                                                RasterCell,
                                                PopulationEntry,
                                                )


class CreateInfrastructureTestdataMixin:
    """Create Testdata for Indicator Tests"""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.scenario = ScenarioFactory(planning_process__owner=cls.profile)

    @classmethod
    def tearDownClass(cls):
        PlanningProcess.objects.all().delete()
        super().tearDownClass()

    @classmethod
    def create_infrastructure_services(cls) -> InfrastructureFactory:
        infrastructure = InfrastructureFactory()
        cls.service1 = ServiceFactory(infrastructure=infrastructure)
        cls.service2 = ServiceFactory(infrastructure=infrastructure)
        return infrastructure

    @classmethod
    def create_areas(cls):
        cls.obj = area_level = AreaLevelFactory(label_field='gen')
        cls.url_pk = cls.obj.pk
        coords = ((-500, 0), (-500, 100), (100, 100), (100, 0), (-500, 0))
        coords = [(x + 1000000, y + 6500000) for x, y in coords]
        cls.area1 = AreaFactory(
            area_level=area_level,
            geom=MultiPolygon(Polygon(coords),
                              srid=3857),
            attributes={'gen': 'area1', },
        )
        coords = ((100, 100), (100, 500), (200, 500), (200, 100), (100, 100))
        coords = [(x + 1000000, y + 6500000) for x, y in coords]
        cls.area2 = AreaFactory(
            area_level=area_level,
            geom=MultiPolygon(Polygon(coords),
                              srid=3857),
            attributes={'gen': 'area2', },
        )
        return cls

    @classmethod
    def create_places(cls, infrastructure: Infrastructure):
        # Places 1 and 2 are in Area1
        cls.place1 = PlaceFactory(infrastructure=infrastructure,
                                  geom=Point(x=1000005, y=6500005))
        cls.place2 = PlaceFactory(infrastructure=infrastructure,
                                  geom=Point(x=1000005, y=6500006))
        # Places 3 and 4 are in Area2
        cls.place3 = PlaceFactory(infrastructure=infrastructure,
                                  geom=Point(x=1000150, y=6500150))
        cls.place4 = PlaceFactory(infrastructure=infrastructure,
                                  geom=Point(x=1000150, y=6500156))
        # Place 5 is in no area
        cls.place5 = PlaceFactory(infrastructure=infrastructure,
                                  geom=Point(x=1000250, y=6500250))

    @classmethod
    def create_capacities(cls):
        CapacityFactory(place=cls.place1, service=cls.service1, capacity=1)
        CapacityFactory(place=cls.place1, service=cls.service2, capacity=2)
        CapacityFactory(place=cls.place2, service=cls.service1, capacity=4)
        # in the scenario, place2 should have no capacity in the base year for service1
        CapacityFactory(place=cls.place2, service=cls.service1,
                        scenario=cls.scenario, capacity=0)
        # but after 2022 it has capacity
        CapacityFactory(place=cls.place2, service=cls.service1,
                        scenario=cls.scenario, capacity=33, from_year=2022)

        # place 2 has only capacity from 2030 for service2
        CapacityFactory(place=cls.place2, service=cls.service2,
                        from_year=2030, capacity=8)

        # in the scenario, place2 should have no capacity from year 2035 for service2
        CapacityFactory(place=cls.place2, service=cls.service2,
                        from_year=2033, scenario=cls.scenario, capacity=16)
        CapacityFactory(place=cls.place2, service=cls.service2,
                        from_year=2035, scenario=cls.scenario, capacity=0)

        # place 3 and 4 have capacity defined for service 1, but place 4 with capacity=0
        CapacityFactory(place=cls.place3, service=cls.service1, capacity=44)
        CapacityFactory(place=cls.place4, service=cls.service1, capacity=0)

        # but between 2025 and 2030 there is capacity in place 4
        CapacityFactory(place=cls.place4, service=cls.service1,
                        from_year=2025, capacity=100)
        CapacityFactory(place=cls.place4, service=cls.service1,
                        from_year=2030, capacity=0)

        # place 5 has capacity defined, but is in no Area
        CapacityFactory(place=cls.place5, service=cls.service1, capacity=66)
        CapacityFactory(place=cls.place5, service=cls.service2, capacity=77)

    @classmethod
    def create_raster_population(cls):
        cls.disaggpopraster = DisaggPopRasterFactory()
        popraster: PopulationRaster = cls.disaggpopraster.popraster
        raster: Raster = popraster.raster

        cells = []
        for n in range(30223, 30228):
            for e in range(42481, 42487):
                cellcode = f'100mN{n:05}E{e:05}'
                cell = RasterCellFactory.build(raster=raster, cellcode=cellcode)
                cells.append(cell)
        RasterCell.objects.bulk_create(cells)

        population = {(30224, 42481): 100, # outside areas
                      (30224, 42482): 200, # area1
                      (30224, 42483): 33, # area1
                      (30224, 42486): 1000, # belongs to area1+area2
                      (30225, 42486): 500, # area2
                      }

        for (e, n), value in population.items():
            cellcode = f'100mN{n:05}E{e:05}'
            RasterCellPopulationFactory(popraster=popraster, cell=cellcode, value=value)

    @classmethod
    def create_years_gender_agegroups(cls):
        """Create years, genders and agegroups"""
        Year.objects.bulk_create([Year(y) for y in range(2020, 2025)])
        cls.years = Year.objects.all()
        Gender.objects.create('Male')
        Gender.objects.create('Female')
        cls.genders = Gender.objects.all()

        AgeGroup.objects.create(from_age=0, to_age=17)
        AgeGroup.objects.create(from_age=18, to_age=64)
        AgeGroup.objects.create(from_age=65, to_age=120)

        cls.age_groups = AgeGroup.objects.all()

    @classmethod
    def creaate_population(cls):
        """create population by area"""
        area_level = cls.area1.area_level
        cls.population = PopulationFactory(area_level=area_level,
                                           year=cls.years[0],
                                           raster=cls.disaggpopraster,
                                           genders=cls.genders,
                                           )

        pop_entry: {'Area1': {[[50, 50],
                               [300, 300],
                               [100, 200]
                               ]},
                    'Area2': {[[70, 50],
                               [350, 300],
                               [150, 200]
                               ]},
                    }

        entries = []
        for area_name, pop_values_by_age_gender in pop_entry.items():
            area = Area.objects.get(name=area_name)
            for a, age_group in cls.age_groups:
                for g, gender in cls.genders:
                    value = pop_values_by_age_gender[a][g]
                    entry = PopulationEntry(population=cls.population,
                                            area=area,
                                            gender=gender,
                                            age_group=age_group,
                                            value=value,
                                            )
            entries.append(entry)
        PopulationEntry.objects.bulk_create(entries)

