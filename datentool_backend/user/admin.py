from django.contrib import admin
from .models import (
    Profile, PlanningProcess, Scenario)
    #, ScenarioPlace, ScenarioCapacity,
    #ScenarioDemandRate)

# Register your models here.
class ProfileAdmin(admin.ModelAdmin):
    """"""


class PlanningProcessAdmin(admin.ModelAdmin):
    """"""


class ScenarioAdmin(admin.ModelAdmin):
    """"""


#class ScenarioPlaceAdmin(admin.ModelAdmin):
    #""""""


#class ScenarioCapacityAdmin(admin.ModelAdmin):
    #""""""


#class ScenarioDemandRateAdmin(admin.ModelAdmin):
    #""""""

admin.site.register(Profile, ProfileAdmin)
admin.site.register(PlanningProcess, PlanningProcessAdmin)
admin.site.register(Scenario, ScenarioAdmin)
#admin.site.register(ScenarioPlace, ScenarioPlaceAdmin)
#admin.site.register(ScenarioCapacity, ScenarioCapacityAdmin)
#admin.site.register(ScenarioDemandRate, ScenarioDemandRateAdmin)
