from django.contrib import admin
from .models import (
    Raster,
    PopulationRaster,
    RasterCell,
    RasterCellPopulation,
    RasterCellPopulationAgeGender,
    Prognosis,
    Population,
    PopulationEntry,
    PopStatistic,
    PopStatEntry,
    Year
    )

admin.site.register(Raster)
admin.site.register(Year)
admin.site.register(PopulationRaster)
admin.site.register(RasterCell)
admin.site.register(RasterCellPopulation)
admin.site.register(RasterCellPopulationAgeGender)
admin.site.register(Prognosis)
admin.site.register(Population)
admin.site.register(PopulationEntry)
admin.site.register(PopStatistic)
admin.site.register(PopStatEntry)
