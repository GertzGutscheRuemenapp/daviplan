from django.db import models
from django.core.validators import MaxLengthValidator
from django.contrib.gis.db import models as gis_models
from ..user.models import Profile
from ..infrastructure.models import Infrastructure, Service
from ..area.models import AreaLevel, Area


class Years(models.Model):
    """years available"""
    year = models.IntegerField()


class Raster(models.Model):
    """a raster"""
    name = models.TextField()
    year = models.ForeignKey(Years, on_delete=models.RESTRICT)


class RasterCell(models.Model):
    """a raster cell"""
    raster = models.ForeignKey(Raster, on_delete=models.RESTRICT)
    cellcode = models.TextField(validators=[MaxLengthValidator(12)])
    value = models.FloatField()


class Gender(models.Model):
    """the genders available"""
    name = models.TextField()


class AgeClassification(models.Model):
    """an age classification"""
    name = models.TextField()


class AgeGroup(models.Model):
    """an age group in an age classification"""
    classification = models.ForeignKey(AgeClassification, on_delete=models.RESTRICT)
    from_age = models.IntegerField()
    to_age = models.IntegerField()


class DisaggPopRaster(models.Model):
    """a raster with disaggregated population by age and gender"""
    genders = models.ManyToManyField(Gender)


class RasterPopulationCell(models.Model):
    """a raster cell with a disaggregated value"""
    raster = models.ForeignKey(DisaggPopRaster, on_delete=models.RESTRICT)
    year = models.IntegerField()
    cell = models.ForeignKey(RasterCell, on_delete=models.RESTRICT)
    age = models.IntegerField()
    gender = models.ForeignKey(Gender, on_delete=models.RESTRICT)
    value = models.FloatField()


class Prognosis(models.Model):
    """a prognosis"""
    name = models.TextField()
    years = models.ManyToManyField(Years)
    raster = models.ForeignKey(DisaggPopRaster, on_delete=models.RESTRICT)
    age_classification = models.ForeignKey(AgeClassification, on_delete=models.RESTRICT)
    is_default = models.BooleanField()


class PrognosisEntry(models.Model):
    """a prognosis entry"""
    prognosis = models.ForeignKey(Prognosis, on_delete=models.RESTRICT)
    year = models.ForeignKey(Years, on_delete=models.RESTRICT)
    area = models.ForeignKey(Area, on_delete=models.RESTRICT)
    agegroup = models.ForeignKey(AgeGroup, on_delete=models.RESTRICT)
    gender = models.ForeignKey(Gender, on_delete=models.RESTRICT)
    value = models.FloatField()


class Population(models.Model):
    """Population data for an area level"""
    area_level = models.ForeignKey(AreaLevel, on_delete=models.RESTRICT)
    year = models.ForeignKey(Years, on_delete=models.RESTRICT)
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
    year = models.ForeignKey(Years, on_delete=models.RESTRICT)


class PopStatEntry(models.Model):
    """statistic entry for an area"""
    popstatistic = models.ForeignKey(PopStatistic, on_delete=models.RESTRICT)
    area = models.ForeignKey(Area, on_delete=models.RESTRICT)
    age = models.IntegerField()
    immigration = models.FloatField()
    emigration = models.FloatField()
    births = models.FloatField()
    deaths = models.FloatField()
