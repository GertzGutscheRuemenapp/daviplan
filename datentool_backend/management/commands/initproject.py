import datetime

from django.core.management.base import BaseCommand
from datentool_backend.area.models import AreaLevel
from datentool_backend.site.models import Year
from datentool_backend.population.models import Gender, Raster, PopulationRaster


class Command(BaseCommand):
    help = 'Start Project with initializing the base tables'

    def add_arguments(self, parser):
        """add additional arguments"""
        #parser.add_argument('poll_ids', nargs='+', type=int)

    def handle(self, *args, **options):
        """handle the command"""

        # add years
        Year.truncate()
        this_year = datetime.date.today().year
        for year in range(Year.MIN_YEAR, this_year):
            Year.objects.create(year=year, is_real=True)
        for year in range(this_year, 2050):
            Year.objects.create(year=year, is_prognosis=True)

        # add genders
        Gender.truncate()
        Gender.objects.create(id=1, name='männlich')
        Gender.objects.create(id=2, name='weiblich')

        # add area levels
        AreaLevel.truncate()
        AreaLevel.objects.create(id=1,
                                 name='Gemeinde',
                                 is_preset=True,
                                 is_default_pop_level=True,
                                 is_statistic_level=True,
                                 is_pop_level=True)
        AreaLevel.objects.create(id=2,
                                 name='Verwaltungsgemeinschaft',
                                 is_preset=True,
                                 )
        AreaLevel.objects.create(id=3,
                                 name='Kreis',
                                 is_preset=True,
                                 )
        AreaLevel.objects.create(id=4,
                                 name='Regierungsbezirk',
                                 is_preset=True,
                                 )
        AreaLevel.objects.create(id=5,
                                 name='Bundesland',
                                 is_preset=True,
                                 )

        # add raster
        Raster.truncate()
        PopulationRaster.truncate()
        raster = Raster.objects.create(id=1, name='LAEA-Raster')
        census_year = Year.objects.get(year=2011)
        PopulationRaster.objects.create(id=1,
                                        raster=raster,
                                        name='Zensus-2011-Raster',
                                        filename='Zensus2011Einwohner100_LAEA3035.tif',
                                        default=True,
                                        year=census_year)

        self.stdout.write(self.style.SUCCESS('Successfully initialized project'))