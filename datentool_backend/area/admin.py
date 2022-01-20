from django.contrib import admin
from .models import (
    AreaLevel, Area, MapSymbol,
    WMSLayer, Source, LayerGroup)

admin.site.register(Source)
admin.site.register(MapSymbol)
admin.site.register(WMSLayer)
admin.site.register(Area)
admin.site.register(AreaLevel)
admin.site.register(LayerGroup)
