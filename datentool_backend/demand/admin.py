from django.contrib import admin
from .models import (AgeGroup, Gender, DemandRateSet, DemandRate, )

admin.site.register(Gender)
admin.site.register(AgeGroup)
admin.site.register(DemandRateSet)
admin.site.register(DemandRate)
