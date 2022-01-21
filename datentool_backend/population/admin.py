from django.contrib import admin
from .models import (Raster, PopulationRaster, RasterCell, RasterCellPopulation,
    Gender, AgeGroup,
    DisaggPopRaster, RasterCellPopulationAgeGender,
    Prognosis, PrognosisEntry,
    Population, PopulationEntry,
    PopStatistic, PopStatEntry,
                     )


@admin.register(Raster)
class RasterAdmin(admin.ModelAdmin):
    """"""


@admin.register(PopulationRaster)
class PopulationRasterAdmin(admin.ModelAdmin):
    """"""


@admin.register(RasterCell)
class RasterCellAdmin(admin.ModelAdmin):
    """"""


@admin.register(RasterCellPopulation)
class RasterCellPopulationAdmin(admin.ModelAdmin):
    """"""


@admin.register(Gender)
class GenderAdmin(admin.ModelAdmin):
    """"""


@admin.register(AgeGroup)
class AgeGroupAdmin(admin.ModelAdmin):
    """"""


@admin.register(DisaggPopRaster)
class DisaggPopRasterAdmin(admin.ModelAdmin):
    """"""


@admin.register(RasterCellPopulationAgeGender)
class RasterCellPopulationAgeGenderAdmin(admin.ModelAdmin):
    """"""


@admin.register(Prognosis)
class PrognosisAdmin(admin.ModelAdmin):
    """"""


@admin.register(PrognosisEntry)
class PrognosisEntryAdmin(admin.ModelAdmin):
    """"""


@admin.register(Population)
class PopulationAdmin(admin.ModelAdmin):
    """"""


@admin.register(PopulationEntry)
class PopulationEntryAdmin(admin.ModelAdmin):
    """"""


@admin.register(PopStatistic)
class PopStatisticAdmin(admin.ModelAdmin):
    """"""


@admin.register(PopStatEntry)
class PopStatEntryAdmin(admin.ModelAdmin):
    """"""
