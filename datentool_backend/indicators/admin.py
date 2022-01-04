from django.contrib import admin
from .models import (
    Mode, ModeVariant, Stop, MatrixCellPlace, MatrixCellStop,
    MatrixPlaceStop, MatrixStopStop, Router, Indicator)

# Register your models here.
class ModesAdmin(admin.ModelAdmin):
    """"""


class ModeVariantAdmin(admin.ModelAdmin):
    """"""


class StopAdmin(admin.ModelAdmin):
    """"""


class MatrixCellPlaceAdmin(admin.ModelAdmin):
    """"""


class MatrixCellStopAdmin(admin.ModelAdmin):
    """"""


class MatrixStopStopAdmin(admin.ModelAdmin):
    """"""


class MatrixPlaceStopAdmin(admin.ModelAdmin):
    """"""


class RouterAdmin(admin.ModelAdmin):
    """"""


class IndicatorAdmin(admin.ModelAdmin):
    """"""


admin.site.register(Mode, ModesAdmin)
admin.site.register(ModeVariant, ModeVariantAdmin)
admin.site.register(Stop, StopAdmin)
admin.site.register(MatrixCellPlace, MatrixCellPlaceAdmin)
admin.site.register(MatrixCellStop, MatrixCellStopAdmin)
admin.site.register(MatrixPlaceStop, MatrixPlaceStopAdmin)
admin.site.register(MatrixStopStop, MatrixStopStopAdmin)
admin.site.register(Router, RouterAdmin)
admin.site.register(Indicator, IndicatorAdmin)
