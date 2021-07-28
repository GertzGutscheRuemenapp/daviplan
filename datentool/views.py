from django.views.generic.base import TemplateView
from datentool_backend.site.models import SiteSettings


class HomePageView(TemplateView):
    template_name = 'home.html'
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        settings = SiteSettings.objects.get_or_create(name='default')[0]
        context['title'] = settings.title
        return context