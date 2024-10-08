from django.contrib import admin
from .models import (
    Stop,
    MatrixCellPlace,
    MatrixCellStop,
    MatrixPlaceStop,
    MatrixStopStop,
    Router,
    ModeVariantStatistic)

admin.site.register(Stop)
admin.site.register(MatrixCellPlace)
admin.site.register(MatrixCellStop)
admin.site.register(MatrixPlaceStop)
admin.site.register(MatrixStopStop)
admin.site.register(Router)
admin.site.register(ModeVariantStatistic)
