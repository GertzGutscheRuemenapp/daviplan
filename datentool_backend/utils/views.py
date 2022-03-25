from django.http import HttpResponseForbidden
from django.db.models import ProtectedError
from django.utils.translation import ugettext as _

from rest_framework import viewsets, status
from rest_framework.response import Response

from drf_spectacular.utils import extend_schema, OpenApiParameter

from .excel_template import ExcelTemplateMixin


class SingletonViewSet(viewsets.ModelViewSet):
    model_class = None

    def retrieve(self, request, *args, **kwargs):
        instance = self.model_class.load()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        instance = self.model_class.load()
        partial = kwargs.pop('partial', False)
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        else:
            return Response(serializer.errors, status=status.HTTP_406_NOT_ACCEPTABLE)


class ProtectCascadeMixin:
    @extend_schema(parameters=[
        OpenApiParameter(name='override_protection', type=bool, required=False,
                         description='''if true, delete depending objects cascadedly,
                         even if they are protected'''),],
                   description='''Delete is not possible if there are depending objects,
                   unless override_protection is passed as query-param''')
    def destroy(self, request, **kwargs):
        """
        try to delete an object. If it is protected,
        because of referencing objects, only delete, if
        override_protection is provided in the request-data or the query_params
        """
        # param to override protection may be in the url or inside the form data
        override_protection = request.query_params.get(
            'override_protection', False) or request.data.get(
            'override_protection', False)
        self.use_protection = override_protection not in ('true', 'True', True)
        try:
            response = super().destroy(request, **kwargs)
        except ProtectedError as err:
            qs = list(err.protected_objects)
            show = 5
            n_objects = len(qs)
            msg_n_referenced = '{} {}:'.format(n_objects,
                                               _('Referencing Object(s)')
                                               )
            msg = '<br/>'.join(list(err.args[:1]) +
                               [msg_n_referenced] +
                               [repr(row).strip('<>') for row in qs[:show]] +
                               ['...' if n_objects > show else '']
                               )
            return HttpResponseForbidden(content=msg)
        return response

    def perform_destroy(self, instance):
        instance.delete(use_protection=self.use_protection)
