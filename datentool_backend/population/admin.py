from django.contrib import admin
from .models import (
    Year, Raster, RasterCell, Gender, AgeClassification,
    AgeGroup, DisaggPopRaster, RasterPopulationCell, Prognosis, PrognosisEntry,
    Population, PopulationEntry,
    PopStatistic, PopStatEntry,
)

# Register your models here.
class YearAdmin(admin.ModelAdmin):
    """"""


class RasterAdmin(admin.ModelAdmin):
    """"""


class GenderAdmin(admin.ModelAdmin):
    """"""


class AgeClassificationAdmin(admin.ModelAdmin):
    """"""


class AgeGroupAdmin(admin.ModelAdmin):
    """"""


class DisaggPopRasterAdmin(admin.ModelAdmin):
    """"""


class RasterPopulationCellAdmin(admin.ModelAdmin):
    """"""


class PrognosisAdmin(admin.ModelAdmin):
    """"""


class PrognosisEntryAdmin(admin.ModelAdmin):
    """"""


class PopulationAdmin(admin.ModelAdmin):
    """"""


class PopulationEntryAdmin(admin.ModelAdmin):
    """"""


class PopStatisticAdmin(admin.ModelAdmin):
    """"""


class PopStatEntryAdmin(admin.ModelAdmin):
    """"""

admin.site.register(Year, YearAdmin)
admin.site.register(Raster, RasterAdmin)
admin.site.register(Gender, GenderAdmin)
admin.site.register(AgeClassification, AgeClassificationAdmin)
admin.site.register(AgeGroup, AgeGroupAdmin)
admin.site.register(DisaggPopRaster, DisaggPopRasterAdmin)
admin.site.register(RasterPopulationCell, RasterPopulationCellAdmin)
admin.site.register(Prognosis, PrognosisAdmin)
admin.site.register(PrognosisEntry, PrognosisEntryAdmin)
admin.site.register(Population, PopulationAdmin)
admin.site.register(PopulationEntry, PopulationEntryAdmin)
admin.site.register(PopStatistic, PopStatisticAdmin)
admin.site.register(PopStatEntry, PopStatEntryAdmin)
