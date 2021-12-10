from django.contrib import admin
from .models import (SiteSetting, ProjectSetting, BaseDataSetting)

admin.site.register(ProjectSetting)
admin.site.register(SiteSetting)
admin.site.register(BaseDataSetting)