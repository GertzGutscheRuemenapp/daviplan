from django.db import models
from django.contrib.gis.db import models as gis_models
from django.core.validators import (MaxLengthValidator,
                                    MinValueValidator, MaxValueValidator)

from datentool_backend.base import NamedModel
from datentool_backend.area.models import AreaLevel, Area
from datentool_backend.user.models import Year
from datentool_backend.utils.protect_cascade import PROTECT_CASCADE
from datentool_backend.base import NamedModel, DatentoolModelMixin

#  Vector tile:
from rest_framework_mvt.managers import MVTManager


class Raster(DatentoolModelMixin, NamedModel, models.Model):
    """a raster"""
    name = models.TextField()


class PopulationRaster(DatentoolModelMixin, NamedModel, models.Model):
    """a raster with population data"""
    name = models.TextField()
    raster = models.ForeignKey(Raster, on_delete=PROTECT_CASCADE)
    year = models.ForeignKey(Year, on_delete=PROTECT_CASCADE)
    default = models.BooleanField(default=False)


class RasterCell(DatentoolModelMixin, models.Model):
    """a raster cell with geometry"""
    raster = models.ForeignKey(Raster, on_delete=PROTECT_CASCADE)
    cellcode = models.TextField(validators=[MaxLengthValidator(13)])
    pnt = gis_models.PointField(srid=3857)
    poly = gis_models.PolygonField(srid=3857)
# vector tile
    #objects = models.Manager()
    #vector_tiles = MVTManager(geo_col='poly')

    def __str__(self) -> str:
        return f'{self.__class__.__name__}: {self.raster.name}-{self.cellcode}'


class RasterCellPopulation(models.Model):
    """the population in a cell in a certain PopulationRaster"""
    popraster = models.ForeignKey(PopulationRaster, on_delete=PROTECT_CASCADE)
    cell = models.ForeignKey(RasterCell, on_delete=PROTECT_CASCADE)
    value = models.FloatField()

    def __str__(self) -> str:
        return f'{self.__class__.__name__}: {self.popraster.name}-{self.cell.cellcode}'


class Gender(DatentoolModelMixin, NamedModel, models.Model):
    """the genders available"""
    name = models.TextField()


class AgeGroup(DatentoolModelMixin, models.Model):
    """an age group in an age classification"""
    from_age = models.IntegerField(validators=[MinValueValidator(0),
                                               MaxValueValidator(127)])
    to_age = models.IntegerField(validators=[MinValueValidator(0),
                                             MaxValueValidator(127)])


class DisaggPopRaster(DatentoolModelMixin, models.Model):
    """a raster with disaggregated population by age and gender"""
    popraster = models.ForeignKey(PopulationRaster,
                               on_delete=PROTECT_CASCADE, null=True)
    genders = models.ManyToManyField(Gender, blank=True)


class RasterCellPopulationAgeGender(models.Model):
    """a raster cell with a disaggregated value"""
    disaggraster = models.ForeignKey(DisaggPopRaster, on_delete=PROTECT_CASCADE)
    year = models.IntegerField()
    cell = models.ForeignKey(RasterCell, on_delete=PROTECT_CASCADE)
    age = models.IntegerField()
    gender = models.ForeignKey(Gender, on_delete=PROTECT_CASCADE)
    value = models.FloatField()


class Prognosis(DatentoolModelMixin, NamedModel, models.Model):
    """a prognosis"""
    name = models.TextField()
    years = models.ManyToManyField(Year, blank=True)
    raster = models.ForeignKey(DisaggPopRaster, on_delete=models.RESTRICT)
    is_default = models.BooleanField()


class PrognosisEntry(models.Model):
    """a prognosis entry"""
    prognosis = models.ForeignKey(Prognosis, on_delete=PROTECT_CASCADE)
    year = models.ForeignKey(Year, on_delete=PROTECT_CASCADE)
    area = models.ForeignKey(Area, on_delete=PROTECT_CASCADE)
    agegroup = models.ForeignKey(AgeGroup, on_delete=PROTECT_CASCADE)
    gender = models.ForeignKey(Gender, on_delete=PROTECT_CASCADE)
    value = models.FloatField()


class Population(DatentoolModelMixin, models.Model):
    """Population data for an area level"""
    area_level = models.ForeignKey(AreaLevel, on_delete=PROTECT_CASCADE)
    year = models.ForeignKey(Year, on_delete=PROTECT_CASCADE)
    genders = models.ManyToManyField(Gender, blank=True)
    raster = models.ForeignKey(DisaggPopRaster, on_delete=PROTECT_CASCADE)


class PopulationEntry(models.Model):
    """population value for a certain area"""
    population = models.ForeignKey(Population, on_delete=PROTECT_CASCADE)
    area = models.ForeignKey(Area, on_delete=PROTECT_CASCADE)
    gender = models.ForeignKey(Gender, on_delete=PROTECT_CASCADE)
    age_group = models.ForeignKey(AgeGroup, on_delete=PROTECT_CASCADE)
    value = models.FloatField()


class PopStatistic(DatentoolModelMixin, models.Model):
    """population statistic for a certain year"""
    year = models.ForeignKey(Year, on_delete=PROTECT_CASCADE)


class PopStatEntry(models.Model):
    """statistic entry for an area"""
    popstatistic = models.ForeignKey(PopStatistic, on_delete=PROTECT_CASCADE)
    area = models.ForeignKey(Area, on_delete=PROTECT_CASCADE)
    immigration = models.FloatField()
    emigration = models.FloatField()
    births = models.FloatField()
    deaths = models.FloatField()

