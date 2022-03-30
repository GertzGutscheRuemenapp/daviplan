from django.db import models, transaction
from django.contrib.gis.db import models as gis_models
from django.core.validators import MaxLengthValidator
from datentool_backend.utils.copy_postgres import DirectCopyManager

from datentool_backend.base import NamedModel, DatentoolModelMixin
from datentool_backend.utils.protect_cascade import PROTECT_CASCADE

from datentool_backend.area.models import Area, AreaLevel
from datentool_backend.user.models import Year
from datentool_backend.demand.models import AgeGroup, Gender


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

    def __str__(self) -> str:
        return f'{self.__class__.__name__}: {self.raster.name}-{self.cellcode}'


class RasterCellPopulation(models.Model):
    """the population in a cell in a certain PopulationRaster"""
    popraster = models.ForeignKey(PopulationRaster, on_delete=PROTECT_CASCADE)
    cell = models.ForeignKey(RasterCell, on_delete=PROTECT_CASCADE)
    value = models.FloatField()
    area = models.ManyToManyField(Area, through='AreaCell')

    def __str__(self) -> str:
        return f'{self.__class__.__name__}: {self.popraster.name}-{self.cell.cellcode}'


class AreaCell(models.Model):
    """
    stores the share of the cell on the whole area population
    and the share of the area on the cells area
    """
    cell = models.ForeignKey(RasterCellPopulation, on_delete=models.CASCADE)
    area = models.ForeignKey(Area, on_delete=models.CASCADE)
    share_cell_of_area = models.FloatField()
    share_area_of_cell = models.FloatField()

    objects = models.Manager()
    copymanager = DirectCopyManager()


class Prognosis(DatentoolModelMixin, NamedModel, models.Model):
    """a prognosis"""
    name = models.TextField()
    is_default = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if self.is_default:
            with transaction.atomic():
                Prognosis.objects.filter(
                    is_default=True).update(is_default=False)
        return super().save(*args, **kwargs)


class Population(DatentoolModelMixin, models.Model):
    """Population data for an area level"""
    year = models.ForeignKey(Year, on_delete=PROTECT_CASCADE)
    genders = models.ManyToManyField(Gender, blank=True)
    prognosis = models.ForeignKey(Prognosis, on_delete=PROTECT_CASCADE, null=True)
    popraster = models.ForeignKey(PopulationRaster,
                               on_delete=PROTECT_CASCADE, null=True)
    arealevels = models.ManyToManyField(AreaLevel, through='PopulationAreaLevel')


class PopulationAreaLevel(models.Model):
    """Population for AreaLevel is up to date"""
    population = models.ForeignKey(Population, on_delete=PROTECT_CASCADE)
    area_level = models.ForeignKey(AreaLevel, on_delete=PROTECT_CASCADE)
    up_to_date = models.BooleanField(default=False)


class PopulationEntry(models.Model):
    """population value for a certain area"""
    objects = models.Manager()
    copymanager = DirectCopyManager()

    population = models.ForeignKey(Population, on_delete=PROTECT_CASCADE)
    area = models.ForeignKey(Area, on_delete=PROTECT_CASCADE)
    gender = models.ForeignKey(Gender, on_delete=PROTECT_CASCADE)
    age_group = models.ForeignKey(AgeGroup, on_delete=PROTECT_CASCADE)
    value = models.FloatField()


class RasterCellPopulationAgeGender(models.Model):
    """a raster cell with a disaggregated value"""
    population = models.ForeignKey(Population, on_delete=PROTECT_CASCADE, null=True)
    cell = models.ForeignKey(RasterCell, on_delete=PROTECT_CASCADE)
    age_group = models.ForeignKey(AgeGroup, on_delete=PROTECT_CASCADE)
    gender = models.ForeignKey(Gender, on_delete=PROTECT_CASCADE)
    value = models.FloatField()

    objects = models.Manager()
    copymanager = DirectCopyManager()


class AreaPopulationAgeGender(models.Model):
    """a raster cell with a disaggregated value"""
    population = models.ForeignKey(Population, on_delete=PROTECT_CASCADE, null=True)
    area = models.ForeignKey(Area, on_delete=PROTECT_CASCADE)
    age_group = models.ForeignKey(AgeGroup, on_delete=PROTECT_CASCADE)
    gender = models.ForeignKey(Gender, on_delete=PROTECT_CASCADE)
    value = models.FloatField()

    objects = models.Manager()
    copymanager = DirectCopyManager()


class PopStatistic(DatentoolModelMixin, models.Model):
    """population statistic for a certain year"""
    year = models.ForeignKey(Year, on_delete=PROTECT_CASCADE)


class PopStatEntry(models.Model):
    """statistic entry for an area"""
    objects = models.Manager()
    copymanager = DirectCopyManager()

    popstatistic = models.ForeignKey(PopStatistic, on_delete=PROTECT_CASCADE)
    area = models.ForeignKey(Area, on_delete=PROTECT_CASCADE)
    immigration = models.FloatField()
    emigration = models.FloatField()
    births = models.FloatField()
    deaths = models.FloatField()

