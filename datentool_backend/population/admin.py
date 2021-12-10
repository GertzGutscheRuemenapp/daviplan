from django.forms import ModelForm
from django.contrib import admin
from .models import (Year, Raster, PopulationRaster, RasterCell, RasterCellPopulation,
    Gender, AgeGroup,
    DisaggPopRaster, RasterCellPopulationAgeGender,
    Prognosis, PrognosisEntry,
    Population, PopulationEntry,
    PopStatistic, PopStatEntry,
)

class YearForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['bm_create_uuid'].required = False

    class Meta:
        model = Year
        fields = '__all__'


# Register your models here.
class YearAdmin(admin.ModelAdmin):
    """"""
    form = YearForm


class RasterAdmin(admin.ModelAdmin):
    """"""


class PopulationRasterAdmin(admin.ModelAdmin):
    """"""


class RasterCellAdmin(admin.ModelAdmin):
    """"""


class RasterCellPopulationAdmin(admin.ModelAdmin):
    """"""


class GenderAdmin(admin.ModelAdmin):
    """"""


class AgeGroupAdmin(admin.ModelAdmin):
    """"""


class DisaggPopRasterAdmin(admin.ModelAdmin):
    """"""


class RasterCellPopulationAgeGenderAdmin(admin.ModelAdmin):
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
admin.site.register(PopulationRaster, PopulationRasterAdmin)
admin.site.register(RasterCell, RasterAdmin)
admin.site.register(RasterCellPopulation, RasterCellPopulationAdmin)
admin.site.register(Gender, GenderAdmin)
admin.site.register(AgeGroup, AgeGroupAdmin)
admin.site.register(DisaggPopRaster, DisaggPopRasterAdmin)
admin.site.register(RasterCellPopulationAgeGender, RasterCellPopulationAgeGenderAdmin)
admin.site.register(Prognosis, PrognosisAdmin)
admin.site.register(PrognosisEntry, PrognosisEntryAdmin)
admin.site.register(Population, PopulationAdmin)
admin.site.register(PopulationEntry, PopulationEntryAdmin)
admin.site.register(PopStatistic, PopStatisticAdmin)
admin.site.register(PopStatEntry, PopStatEntryAdmin)
