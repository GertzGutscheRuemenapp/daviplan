from django.core.management.base import BaseCommand
from datentool_backend.area.models import (AreaLevel, MapSymbol, Source,
                                           SourceTypes, AreaField, FieldType,
                                           FieldTypes)
from datentool_backend.population.models import Gender, Raster, PopulationRaster
from datentool_backend.modes.models import ModeVariant, Mode


class Command(BaseCommand):
    help = 'Start Project with initializing the base tables'

    def add_arguments(self, parser):
        """add additional arguments"""
        #parser.add_argument('poll_ids', nargs='+', type=int)

    def handle(self, *args, **options):
        """handle the command"""

        '''
        # add years
        Year.truncate()
        this_year = datetime.date.today().year
        for year in range(Year.MIN_YEAR, this_year):
            Year.objects.create(year=year, is_real=True)
        for year in range(this_year, 2050):
            Year.objects.create(year=year, is_prognosis=True)
        '''

        # add genders
        Gender.truncate()
        Gender.objects.create(id=1, name='männlich')
        Gender.objects.create(id=2, name='weiblich')

        # generic field types
        FieldType.truncate()
        str_field = FieldType.objects.create(name='Zeichenkette',
                                             is_preset=True,
                                             ftype=FieldTypes.STRING)
        FieldType.objects.create(name='Zahl',
                                 is_preset=True,
                                 ftype=FieldTypes.NUMBER)

        # area levels with BKG API URLs
        AreaLevel.truncate()
        symbol = MapSymbol.objects.create(symbol=MapSymbol.Symbol.LINE,
                                          stroke_color='yellow')
        source = Source.objects.create(
            url='https://sgx.geodatenzentrum.de/wfs_vg250',
            layer='vg250_gem',
            source_type=SourceTypes.WFS
        )
        gem = AreaLevel.objects.create(id=1,
                                       name='Gemeinden',
                                       symbol=symbol,
                                       source=source,
                                       is_preset=True,
                                       is_default_pop_level=True,
                                       is_statistic_level=True,
                                       is_pop_level=True,
                                       order=3)

        symbol = MapSymbol.objects.create(symbol=MapSymbol.Symbol.LINE,
                                          stroke_color='red')
        source = Source.objects.create(
            url='https://sgx.geodatenzentrum.de/wfs_vg250',
            layer='vg250_vwg',
            source_type=SourceTypes.WFS
        )
        vwg = AreaLevel.objects.create(id=2,
                                       name='Verwaltungsgemeinschaften',
                                       symbol=symbol,
                                       source=source,
                                       is_preset=True,
                                       order=2
                                       )

        symbol = MapSymbol.objects.create(symbol=MapSymbol.Symbol.LINE,
                                          stroke_color='green')
        source = Source.objects.create(
            url='https://sgx.geodatenzentrum.de/wfs_vg250',
            layer='vg250_krs',
            source_type=SourceTypes.WFS
        )
        krs = AreaLevel.objects.create(id=3,
                                       name='Kreise',
                                       symbol=symbol,
                                       source=source,
                                       is_preset=True,
                                       order=1
                                       )

        symbol = MapSymbol.objects.create(symbol=MapSymbol.Symbol.LINE,
                                          stroke_color='black')
        source = Source.objects.create(
            url='https://sgx.geodatenzentrum.de/wfs_vg250',
            layer='vg250_lan',
            source_type=SourceTypes.WFS
        )
        lan = AreaLevel.objects.create(id=4,
                                       name='Bundesländer',
                                       symbol=symbol,
                                       source=source,
                                       is_preset=True,
                                       order=0
                                       )


        # label and key fields for each level (as provided by BKG API)
        levels = {gem: ('gen', 'ags'),
                  vwg: ('gen', 'ars'),
                  krs: ('gen', 'ags'),
                  lan: ('gen', 'ags'),
                  }
        for level, (label_field, key_field) in levels.items():
            AreaField.objects.create(area_level=level, name=label_field,
                                     is_label=True, field_type=str_field)
            AreaField.objects.create(area_level=level, name=key_field,
                                     is_key=True, field_type=str_field)

        # add raster
        Raster.truncate()
        PopulationRaster.truncate()
        raster = Raster.objects.create(id=1, name='LAEA-Raster')
        PopulationRaster.objects.create(id=1,
                                        raster=raster,
                                        name='Zensus-2011-Raster',
                                        filename='Zensus2011Einwohner100_LAEA3035.tif',
                                        default=True)

        # add mode variants
        ModeVariant.truncate()
        ModeVariant.objects.create(id=1, mode=Mode.WALK,
                                   label=Mode.WALK.label, is_default=True)
        ModeVariant.objects.create(id=2, mode=Mode.BIKE,
                                   label=Mode.BIKE.label, is_default=True)
        ModeVariant.objects.create(id=3, mode=Mode.CAR,
                                   label=Mode.CAR.label, is_default=True)
        ModeVariant.objects.create(id=4, mode=Mode.TRANSIT,
                                   label=Mode.TRANSIT.label, is_default=True)

        self.stdout.write(self.style.SUCCESS('Successfully initialized project'))
