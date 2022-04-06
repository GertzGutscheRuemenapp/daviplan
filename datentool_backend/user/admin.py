from django.contrib import admin
from .models.profile import Profile
from .models.process import PlanningProcess, Scenario

admin.site.register(Profile)
admin.site.register(PlanningProcess)
admin.site.register(Scenario)
