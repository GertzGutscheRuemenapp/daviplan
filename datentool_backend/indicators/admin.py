from django.contrib import admin
from .models import (
    Mode, ModeVariant, Stop, MatrixCellPlace, MatrixCellStop,
    MatrixPlaceStop, MatrixStopStop, Router, Indicator)

admin.site.register(Mode)
admin.site.register(ModeVariant)
admin.site.register(Stop)
admin.site.register(MatrixCellPlace)
admin.site.register(MatrixCellStop)
admin.site.register(MatrixPlaceStop)
admin.site.register(MatrixStopStop)
admin.site.register(Router)
admin.site.register(Indicator)
