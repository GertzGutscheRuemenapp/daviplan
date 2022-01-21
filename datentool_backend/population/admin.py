from django.contrib import admin
from .models import (
    Raster,
    PopulationRaster,
    RasterCell,
    RasterCellPopulation,
    Gender,
    AgeGroup,
    DisaggPopRaster,
    RasterCellPopulationAgeGender,
    Prognosis,
    PrognosisEntry,
    Population,
    PopulationEntry,
    PopStatistic,
    PopStatEntry,
    )

admin.site.register(Raster)
admin.site.register(PopulationRaster)
admin.site.register(RasterCell)
admin.site.register(RasterCellPopulation)
admin.site.register(Gender)
admin.site.register(AgeGroup)
admin.site.register(DisaggPopRaster)
admin.site.register(RasterCellPopulationAgeGender)
admin.site.register(Prognosis)
admin.site.register(PrognosisEntry)
admin.site.register(Population)
admin.site.register(PopulationEntry)
admin.site.register(PopStatistic)
admin.site.register(PopStatEntry)
