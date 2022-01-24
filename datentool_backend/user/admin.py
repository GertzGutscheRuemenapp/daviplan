from django.contrib import admin
from .models import (Profile, Year, PlanningProcess, Infrastructure, Service)


admin.site.register(Profile)
admin.site.register(Year)
admin.site.register(PlanningProcess)
admin.site.register(Infrastructure)
admin.site.register(Service)
