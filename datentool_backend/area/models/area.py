from django.db import models
from django.db.models import (TextField, F, OuterRef, Subquery,
                              Prefetch, Value,
                              Case, When)
from django.db.models.functions import Cast, Coalesce, Concat
from django.db.models.signals import post_save
from django.contrib.gis.db import models as gis_models

from datentool_backend.utils.protect_cascade import PROTECT_CASCADE
from datentool_backend.base import NamedModel, DatentoolModelMixin
from .area_level import AreaLevel, AreaField, FieldTypes, FieldType, FClass


class Area(DatentoolModelMixin, models.Model):
    """an area"""
    CUT_OUT_SUFFIX = '(Ausschnitt)'
    area_level = models.ForeignKey(AreaLevel, on_delete=PROTECT_CASCADE)
    # flag that is set when parts were cut while intersecting with project area
    is_cut = models.BooleanField(default=False)
    geom = gis_models.MultiPolygonField(srid=3857)

    @property
    def attributes(self):
        return self.areaattribute_set

    def get_attr_value(self, attr: str):
        """get the value of an attribute"""
        return self.attributes.get(field__name=attr).value

    @classmethod
    def label_annotated_qs(cls, area_level: AreaLevel) -> 'Area':
        attributes = AreaAttribute.value_annotated_qs()
        area_attributes = attributes.filter(area=OuterRef('pk'))
        area_fields = AreaField.objects.filter(area_level=area_level)
        area_field_names =  ','.join(area_fields.values_list('name', flat=True))
        area_field_names = f"'{area_field_names}'"

        annotations = {area_field.name: Subquery(area_attributes
                                                 .filter(field=area_field)
                                                 .values('_value')[:1])
                       for area_field in area_fields}

        try:
            label_field = area_fields.get(is_label=True)
            label_attribute = area_attributes.filter(field=label_field)
            annotations['_label0'] = Subquery(label_attribute.values('_value')[:1]
             )

        except AreaField.DoesNotExist:
            annotations['_label0'] = Value('')

        try:
            key_field = area_fields.get(is_key=True)
            key_attribute = area_attributes.filter(field=key_field)
            annotations['_key'] = Subquery(key_attribute.values('_value')[:1])
        except AreaField.DoesNotExist:
            annotations['_key'] = Value('')

        annotations['_field_names'] = Value(area_field_names)

        label_annotation = Case(When(is_cut=True,
                                          then=Concat(F('_label0'),
                                                      Value(' (Ausschnitt)'))),
                                     default=F('_label0'),
                                output_field=models.TextField())

        qs = cls.objects\
            .filter(area_level_id=area_level)\
            .prefetch_related('area_level')\
            .prefetch_related(
                Prefetch('areaattribute_set', queryset=attributes))\
            .annotate(**annotations)\
            .annotate(_label=label_annotation)

        return qs

    @classmethod
    def annotated_qs(cls, area_level: AreaLevel) -> 'Area':
        attributes = AreaAttribute.value_annotated_qs()
        area_attributes = attributes.filter(area=OuterRef('pk'))
        area_fields = AreaField.objects.filter(area_level=area_level)
        annotations = {area_field.name: Subquery(area_attributes\
                                                 .filter(field=area_field)\
                                                 .values('_value')[:1])
                       for area_field in area_fields}
        qs=cls.objects\
            .filter(area_level=area_level)\
            .prefetch_related('area_level')\
            .prefetch_related(
                Prefetch('areaattribute_set', queryset=attributes))\
            .annotate(**annotations)
        return qs

    @property
    def key(self):
        """The Area key"""
        if hasattr(self, '_key'):
            return self._key
        try:
            key_attr = self.areaattribute_set.get(field__is_key=True)
        except AreaAttribute.DoesNotExist:
            return ''
        return str(key_attr.value)

    @property
    def label(self):
        """The area label retrieved from the attributes"""
        if hasattr(self, '_label'):
            return self._label
        try:
            label_attr = self.areaattribute_set.get(field__is_label=True)
        except AreaAttribute.DoesNotExist:
            return ''
        label = str(label_attr.value)
        if self.is_cut:
            label += ' (Ausschnitt)'
        return label

    @attributes.setter
    def attributes(self, attr_dict: dict):
        if not self.pk:
            self._attr_dict = attr_dict
            return
        aa = AreaAttribute.objects.filter(area=self)
        aa.delete()
        for field_name, value in attr_dict.items():
            try:
                field = AreaField.objects.get(area_level=self.area_level,
                                              name=field_name)
            except AreaField.DoesNotExist:
                if isinstance(value, (int, float)):
                    ftype = FieldTypes.NUMBER
                else:
                    ftype = FieldTypes.STRING
                try:
                    field_type = FieldType.objects.get(ftype=ftype)
                except FieldType.DoesNotExist:
                    field_type = FieldType.objects.create(ftype=ftype,
                                                          name=ftype.value)
                field = AreaField.objects.create(area_level=self.area_level,
                                                 name=field_name,
                                                 field_type=field_type,
                                                 )
            AreaAttribute.objects.create(area=self, field=field, value=value)

    @property
    def field_names(self):
        if hasattr(self, '_field_names'):
            return self._field_names
        area_fields = AreaField.objects.filter(area_level=self.area_level)
        area_field_names = ','.join(area_fields.values_list('name', flat=True))
        return area_field_names

    @staticmethod
    def post_create(sender, instance, created, *args, **kwargs):
        if not created:
            return
        if hasattr(instance, '_attr_dict'):
            instance.attributes = instance._attr_dict

    def __str__(self) -> str:
        return f'{self.__class__.__name__} ({self.area_level.name}): {self.label}'


post_save.connect(Area.post_create, sender=Area)


class FieldAttribute(DatentoolModelMixin, NamedModel, models.Model):
    """a value of an Area"""
    str_value = models.TextField(null=True)
    num_value = models.FloatField(null=True)
    class_value = models.ForeignKey(FClass, null=True, on_delete=PROTECT_CASCADE)

    class Meta:
        abstract = True

    @classmethod
    def value_annotated_qs(cls) -> 'FieldAttribute':
        """returns a queryset annotated with the value"""
        qs = cls.objects\
            .select_related('field__field_type', 'class_value')\
            .annotate(_value=Coalesce(F('str_value'),
                                      Coalesce(Cast(F('num_value'), TextField()),
                                               F('class_value__value'))))
        return qs

    @property
    def value(self):
        """represent the the Attribute-instance depending on the field_type"""
        if hasattr(self, '_value'):
            return self._value
        if self.field.field_type.ftype == FieldTypes.NUMBER:
            return self.num_value
        elif self.field.field_type.ftype == FieldTypes.STRING:
            return self.str_value
        elif self.field.field_type.ftype == FieldTypes.CLASSIFICATION:
            return self.class_value.value

    @value.setter
    def value(self, data):
        """convert the data depending on the field_type"""
        if self.field.field_type.ftype == FieldTypes.NUMBER:
            self.num_value = float(data)
        elif self.field.field_type.ftype == FieldTypes.STRING:
            self.str_value = data
        elif self.field.field_type.ftype == FieldTypes.CLASSIFICATION:
            try:
                fclass = FClass.objects.get(ftype=self.field.field_type,
                                            value=data)
            except FClass.DoesNotExist:
                raise ValueError(f'{data} for field {self.field.name} is no valid value')
            self.class_value = fclass

    def __repr__(self) -> str:
        return f'{self.field.name}:{self.value}'

    def __str__(self) -> str:
        return f'{self.__class__.__name__}: {self.field.name}:{self.value}'


class AreaAttribute(FieldAttribute):
    area = models.ForeignKey(Area, on_delete=models.CASCADE)
    field = models.ForeignKey(AreaField, on_delete=PROTECT_CASCADE)

    class Meta:
        unique_together = [['area', 'field']]

    @classmethod
    def value_annotated_qs(cls) -> 'AreaAttribute':
        """returns a queryset annotated with the value"""
        qs = super().value_annotated_qs()
        qs = qs.annotate(is_label=F('field__is_label'),
                         is_key=F('field__is_key'),
                         field_name=F('field__name'))
        return qs
