from django.contrib import admin
from .models import (
    Mode, ModeVariant, ReachabilityMatrix, Router, Indicator)

# Register your models here.
class ModesAdmin(admin.ModelAdmin):
    """"""


class ModeVariantAdmin(admin.ModelAdmin):
    """"""


class ReachabilityMatrixAdmin(admin.ModelAdmin):
    """"""


class RouterAdmin(admin.ModelAdmin):
    """"""


class IndicatorAdmin(admin.ModelAdmin):
    """"""


admin.site.register(Mode, ModesAdmin)
admin.site.register(ModeVariant, ModeVariantAdmin)
admin.site.register(ReachabilityMatrix, ReachabilityMatrixAdmin)
admin.site.register(Router, RouterAdmin)
admin.site.register(Indicator, IndicatorAdmin)
