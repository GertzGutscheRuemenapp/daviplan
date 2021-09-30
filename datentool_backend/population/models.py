from django.db import models
from django.contrib.gis.db import models as gis_models
from django.core.validators import (MaxLengthValidator,
                                    MinValueValidator, MaxValueValidator)

from datentool_backend.base import NamedModel
from datentool_backend.area.models import AreaLevel, Area
from bulkmodel.models import BulkModel


class Year(BulkModel):
    """years available"""
    year = models.IntegerField()

    def __str__(self) -> str:
        return f'{self.__class__.__name__}: {self.year}'


class Raster(NamedModel, models.Model):
    """a raster"""
    name = models.TextField()


class PopulationRaster(NamedModel, models.Model):
    """a raster with population data"""
    name = models.TextField()
    raster = models.ForeignKey(Raster, on_delete=models.RESTRICT)
    year = models.ForeignKey(Year, on_delete=models.RESTRICT)
    default = models.BooleanField(default=False)


class RasterCell(models.Model):
    """a raster cell with geometry"""
    raster = models.ForeignKey(Raster, on_delete=models.RESTRICT)
    cellcode = models.TextField(validators=[MaxLengthValidator(13)])
    pnt = gis_models.PointField()
    poly = gis_models.PolygonField()


class RasterCellPopulation(models.Model):
    """the population in a cell in a certain PopulationRaster"""
    raster = models.ForeignKey(PopulationRaster, on_delete=models.RESTRICT)
    cell = models.ForeignKey(RasterCell, on_delete=models.RESTRICT)
    value = models.FloatField()


class Gender(NamedModel, models.Model):
    """the genders available"""
    name = models.TextField()


class AgeClassification(NamedModel, models.Model):
    """an age classification"""
    name = models.TextField()


class AgeGroup(models.Model):
    """an age group in an age classification"""
    classification = models.ForeignKey(AgeClassification, on_delete=models.RESTRICT)
    from_age = models.IntegerField(validators=[MinValueValidator(0),
                                               MaxValueValidator(127)])
    to_age = models.IntegerField(validators=[MinValueValidator(0),
                                             MaxValueValidator(127)])


class DisaggPopRaster(models.Model):
    """a raster with disaggregated population by age and gender"""
    raster = models.ForeignKey(PopulationRaster,
                               on_delete=models.RESTRICT, null=True)
    genders = models.ManyToManyField(Gender)


class RasterCellPopulationAgeGender(models.Model):
    """a raster cell with a disaggregated value"""
    raster = models.ForeignKey(DisaggPopRaster, on_delete=models.RESTRICT)
    year = models.IntegerField()
    cell = models.ForeignKey(RasterCell, on_delete=models.RESTRICT)
    age = models.IntegerField()
    gender = models.ForeignKey(Gender, on_delete=models.RESTRICT)
    value = models.FloatField()


class Prognosis(NamedModel, models.Model):
    """a prognosis"""
    name = models.TextField()
    years = models.ManyToManyField(Year)
    raster = models.ForeignKey(DisaggPopRaster, on_delete=models.RESTRICT)
    age_classification = models.ForeignKey(AgeClassification, on_delete=models.RESTRICT)
    is_default = models.BooleanField()


class PrognosisEntry(models.Model):
    """a prognosis entry"""
    prognosis = models.ForeignKey(Prognosis, on_delete=models.RESTRICT)
    year = models.ForeignKey(Year, on_delete=models.RESTRICT)
    area = models.ForeignKey(Area, on_delete=models.RESTRICT)
    agegroup = models.ForeignKey(AgeGroup, on_delete=models.RESTRICT)
    gender = models.ForeignKey(Gender, on_delete=models.RESTRICT)
    value = models.FloatField()


class Population(models.Model):
    """Population data for an area level"""
    area_level = models.ForeignKey(AreaLevel, on_delete=models.RESTRICT)
    year = models.ForeignKey(Year, on_delete=models.RESTRICT)
    genders = models.ManyToManyField(Gender)
    raster = models.ForeignKey(DisaggPopRaster, on_delete=models.RESTRICT)


class PopulationEntry(models.Model):
    """population value for a certain area"""
    population = models.ForeignKey(Population, on_delete=models.RESTRICT)
    area = models.ForeignKey(Area, on_delete=models.RESTRICT)
    gender = models.ForeignKey(Gender, on_delete=models.RESTRICT)
    # age or agegroup???
    value = models.FloatField()


class PopStatistic(models.Model):
    """population statistic for a certain year"""
    year = models.ForeignKey(Year, on_delete=models.RESTRICT)


class PopStatEntry(models.Model):
    """statistic entry for an area"""
    popstatistic = models.ForeignKey(PopStatistic, on_delete=models.RESTRICT)
    area = models.ForeignKey(Area, on_delete=models.RESTRICT)
    age = models.IntegerField()
    immigration = models.FloatField()
    emigration = models.FloatField()
    births = models.FloatField()
    deaths = models.FloatField()
