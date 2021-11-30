from django.contrib import admin
from .models import (
    Profile, Project, Scenario)

# Register your models here.
class ProfileAdmin(admin.ModelAdmin):
    """"""


class ProjectAdmin(admin.ModelAdmin):
    """"""


class ScenarioAdmin(admin.ModelAdmin):
    """"""


admin.site.register(Profile, ProfileAdmin)
admin.site.register(Project, ProjectAdmin)
admin.site.register(Scenario, ScenarioAdmin)
