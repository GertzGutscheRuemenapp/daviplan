from django.contrib import admin
from datentool_backend.area.models import (
    AreaLevel, Area, SymbolForm, MapSymbol,
    WMSLayer, InternalWFSLayer, Source, )

# Register your models here.
class SourceAdmin(admin.ModelAdmin):
    """"""


class InternalWFSLayerAdmin(admin.ModelAdmin):
    """"""


class MapSymbolsAdmin(admin.ModelAdmin):
    """"""


class SymbolFormAdmin(admin.ModelAdmin):
    """"""


class WMSLayerAdmin(admin.ModelAdmin):
    """"""


class AreaAdmin(admin.ModelAdmin):
    """"""


class AreaLevelAdmin(admin.ModelAdmin):
    """"""


admin.site.register(Source, SourceAdmin)
admin.site.register(InternalWFSLayer, InternalWFSLayerAdmin)
admin.site.register(MapSymbol, MapSymbolsAdmin)
admin.site.register(SymbolForm, SymbolFormAdmin)
admin.site.register(WMSLayer, WMSLayerAdmin)
admin.site.register(Area, AreaAdmin)
admin.site.register(AreaLevel, AreaLevelAdmin)
