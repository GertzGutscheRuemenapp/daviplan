from django.views.generic.base import TemplateView
from datentool_backend.site.models import SiteSetting
from django.conf import settings


class HomePageView(TemplateView):
    template_name = 'home.html'
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        site_settings, created = SiteSetting.objects.get_or_create(pk=1)
        #css = [v for k, v in settings.ANGULAR_RESOURCES.items()
               #if v.endswith('css')]
        #scripts = [v for k, v in settings.ANGULAR_RESOURCES.items()
                   #if v.endswith('js')]
        context['title'] = site_settings.title
        context.update(settings.ANGULAR_RESOURCES)
        return context
