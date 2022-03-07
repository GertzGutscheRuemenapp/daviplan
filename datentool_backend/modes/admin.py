from django.contrib import admin
from .models import (
     ModeVariant, CutOffTime)

admin.site.register(ModeVariant)
admin.site.register(CutOffTime)
