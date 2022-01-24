from django.contrib import admin
from .models import (
    Mode, ModeVariant, CutOffTime)

admin.site.register(Mode)
admin.site.register(ModeVariant)
admin.site.register(CutOffTime)
