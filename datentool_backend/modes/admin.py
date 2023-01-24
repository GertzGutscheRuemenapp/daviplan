from django.contrib import admin
from .models import (ModeVariant, CutOffTime, Network)

admin.site.register(Network)
admin.site.register(ModeVariant)
admin.site.register(CutOffTime)
