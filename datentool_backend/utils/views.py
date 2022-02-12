from rest_framework import viewsets, status
from django.contrib.auth.mixins import UserPassesTestMixin
from django.http import (HttpResponse,
                         HttpResponseForbidden,
                         JsonResponse,
                         )
from django.db.models import ProtectedError
from django.utils.translation import ugettext as _
from abc import ABC
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.utils.serializer_helpers import ReturnDict
from drf_spectacular.utils import extend_schema, OpenApiParameter
from datentool_backend.utils.serializers import (BulkValidationError, )


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


class PostGetViewMixin:
    """
    mixin for querying resources with POST method to be able to put parameters
    into the body,
    the query parameter 'GET=true' when posting signals derived views to call
    post_get function to look into the body for parameters and to behave like
    when receiving a GET request (no creation of objects then)
    WARNING: contradicts the RESTful API, so use only when query parameters
    are getting too big (browsers have technical restrictions for the
    length of an url)
    """
    def create(self, request, **kwargs):
        if self.isGET:
            return self.post_get(request, **kwargs)
        return super().create(request, **kwargs)

    @property
    def isGET(self):
        if self.request.method == 'GET':
            return True
        post_get = self.request.query_params.get('GET', False)
        if (post_get and post_get in ['True', 'true']):
            return True
        return False

    def post_get(self, request, **kwargs):
        """
        override this, should return serialized data of requested resources
        """
        return super().list(request, **kwargs)


class CasestudyReadOnlyViewSetMixin(ABC):
    """
    This Mixin provides general list and create methods filtering by
    lookup arguments and query-parameters matching fields of the requested objects

    class-variables
    --------------
       additional_filters - dict, keyword arguments for additional filters
    """
    additional_filters = {}
    serializer_class = None
    serializers = {}
    pagination_class = None

    def get_serializer_class(self):
        return self.serializers.get(self.action,
                                    self.serializer_class)



    def list(self, request, **kwargs):
        SerializerClass = self.get_serializer_class()

        # special format requested -> let the plugin handle that
        if ('format' in request.query_params):
            return super().list(request, **kwargs)

        queryset = self._filter(kwargs, query_params=request.query_params,
                                SerializerClass=SerializerClass)
        if queryset is None:
            return Response(status=400)
        if self.pagination_class:
            paginator = self.pagination_class()
            queryset = paginator.paginate_queryset(queryset, request)

        serializer = SerializerClass(queryset, many=True,
                                     context={'request': request, })

        data = self.filter_fields(serializer, request)
        if self.pagination_class:
            return paginator.get_paginated_response(data)
        return Response(data)

    def retrieve(self, request, **kwargs):
        SerializerClass = self.get_serializer_class()
        pk = kwargs.pop('pk')
        queryset = self._filter(kwargs, query_params=request.query_params,
                                SerializerClass=SerializerClass)
        model = get_object_or_404(queryset, pk=pk)
        serializer = SerializerClass(model, context={'request': request})
        data = self.filter_fields(serializer, request)
        return Response(data)

    @staticmethod
    def filter_fields(serializer, request):
        """
        limit amount of fields of response by optional query parameter 'field'
        """
        data = serializer.data
        fields = request.query_params.getlist('field')
        if fields:
            if isinstance(data, ReturnDict):
                data = {k: v for k, v in data.items() if k in fields}
            else:
                data = [{k: v for k, v in row.items() if k in fields}
                        for row in data]
        return data

    def _filter(self, lookup_args, query_params=None, SerializerClass=None,
                annotations=None):
        """
        return a queryset filtered by lookup arguments and query parameters
        return None if query parameters are malformed
        """
        SerializerClass = SerializerClass or self.get_serializer_class()
        # filter the lookup arguments
        filter_args = {v: lookup_args[k] for k, v
                       in SerializerClass.parent_lookup_kwargs.items()}

        queryset = self.get_queryset()
        # filter additional expressions
        filter_args.update(self.get_filter_args(queryset=queryset,
                                                query_params=query_params)
                           )
        queryset = queryset.filter(**filter_args)

        return queryset

    def get_filter_args(self, queryset, query_params=None):
        """
        get filter arguments defined by the query_params
        and by additional filters
        """
        # filter any query parameters matching fields of the model
        filter_args = {k: v for k, v in self.additional_filters.items()}
        if not query_params:
            return filter_args
        for k, v in query_params.items():
            key_cmp = k.split('__')
            key = key_cmp[0]
            is_attr = (hasattr(queryset.model, key) or
                       key in queryset.query.annotations)
            if is_attr:
                if len(key_cmp) > 1:
                    cmp = key_cmp[-1]
                    if cmp == 'in':
                        v = v.strip('[]').split(',')
                filter_args[k] = v
        return filter_args


class CasestudyViewSetMixin(CasestudyReadOnlyViewSetMixin):
    """
    This Mixin provides general list and create methods filtering by
    lookup arguments and query-parameters matching fields of the requested objects

    class-variables
    --------------
       casestudy_only - if True, get only items of the current casestudy
       additional_filters - dict, keyword arguments for additional filters
    """
    def create(self, request, **kwargs):
        """check permission for casestudy"""
        try:
            return super().create(request, **kwargs)
        except BulkValidationError as e:
            return self.error_response(e.message, file_url=e.path)

    def error_response(self, message, file_url=None):
        res = { 'message': message }
        if file_url:
            res['file_url'] = file_url
        response = JsonResponse(res, status=400)
        return response

    def perform_create(self, serializer):
        url_pks = serializer.context['request'].session['url_pks']
        new_kwargs = {}
        for k, v in url_pks.items():
            if k not in self.serializer_class.parent_lookup_kwargs:
                continue
            key = self.serializer_class.parent_lookup_kwargs[k].replace('__id', '_id')
            if '__' in key:
                continue
            new_kwargs[key] = v
        serializer.save(**new_kwargs)

    def list(self, request, **kwargs):
        if request.query_params.get('request', None) == 'template':
            serializer = self.serializers.get('create', None)
            if serializer and hasattr(serializer, 'create_template'):
                content = serializer.create_template()
                response = HttpResponse(
                    content_type=(
                        'application/vnd.openxmlformats-officedocument.'
                        'spreadsheetml.sheet'
                    )
                )
                response['Content-Disposition'] = \
                    'attachment; filename=template.xlsx'
                response.write(content)
                return response
        return super().list(request, **kwargs)


class ReadOnlyAccess(UserPassesTestMixin):
    """no write permission, user with "can edit_basedata" or "admin_access" can read_only"""

    def test_func(self):
        if (self.request.method in permissions.SAFE_METHODS and
                self.request.user.is_authenticated):
            return True
        if (self.request.user.is_superuser == True and
                self.request.method in permissions.SAFE_METHODS):
            return True
        if (self.request.method in permissions.SAFE_METHODS and
            (self.request.user.profile.admin_access or
             self.request.user.profile.can_edit_basedata)):
            return True


