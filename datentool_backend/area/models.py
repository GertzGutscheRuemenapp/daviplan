from django.db import models
from django.contrib.gis.db import models as gis_models
from datentool_backend.base import NamedModel, JsonAttributes
from datentool_backend.utils.protect_cascade import PROTECT_CASCADE
from datentool_backend.base import NamedModel, DatentoolModelMixin


class MapSymbol(DatentoolModelMixin, models.Model):
    '''
    MapSymbols
    '''
    class Symbol(models.TextChoices):
        LINE = 'line'
        CIRCLE = 'circle'
        SQUARE = 'square'
        STAR = 'star'

    symbol = models.CharField(max_length=9, choices=Symbol.choices,
                              default=Symbol.CIRCLE)
    fill_color = models.CharField(max_length=9, default='#FFFFFF')
    stroke_color = models.CharField(max_length=9, default='#000000')


class LayerGroup(DatentoolModelMixin, NamedModel, models.Model):
    """a Layer Group"""
    name = models.TextField()
    order = models.IntegerField(default=0)
    external = models.BooleanField(default=False)


class Layer(DatentoolModelMixin, NamedModel, models.Model):
    """a generic layer"""
    name = models.TextField()
    active =  models.BooleanField(default=False)
    group = models.ForeignKey(LayerGroup, on_delete=PROTECT_CASCADE)
    layer_name = models.TextField()
    order = models.IntegerField(default=0)
    description = models.TextField(default='', blank=True)

    class Meta:
        abstract = True


class WMSLayer(Layer):
    """a WMS Layer"""
    url = models.URLField()

    def __str__(self) -> str:
        return f'{self.__class__.__name__}: {self.url}'


class SourceTypes(models.TextChoices):
    """SourceTypes"""
    WFS = 'WFS', 'WFS Source'
    FILE = 'FILE', 'File Source'


class Source(DatentoolModelMixin, models.Model):
    """a generic source"""
    source_type = models.CharField(max_length=4, choices=SourceTypes.choices)
    date = models.DateField()
    id_field = models.TextField()
    url = models.URLField(null=True, blank=True)
    layer = models.TextField(null=True, blank=True)


class AreaLevel(DatentoolModelMixin, NamedModel, models.Model):
    """an area level"""
    name = models.TextField()
    order = models.IntegerField(unique=False, default=0)
    symbol = models.OneToOneField(MapSymbol, on_delete=models.SET_NULL,
                                  null=True, blank=True)
    source = models.OneToOneField(Source, on_delete=models.SET_NULL, null=True,
                                  blank=True)
    is_active = models.BooleanField(default=True)
    is_preset = models.BooleanField(default=False)
    label_field = models.TextField(null=True)


class Area(DatentoolModelMixin, JsonAttributes, models.Model):
    """an area"""
    area_level = models.ForeignKey(AreaLevel, on_delete=PROTECT_CASCADE)
    geom = gis_models.MultiPolygonField(srid=3857)

    def __str__(self) -> str:
        attributes = self.areaattribute_set
        name = attributes.get('field__name' == self.area_level.label_field).field.name
        return f'{self.__class__.__name__} ({self.area_level.name}): {name}'


class FieldTypes(models.TextChoices):
    """enum for field types"""
    CLASSIFICATION = 'CLA', 'Classification'
    NUMBER = 'NUM', 'Number'
    STRING = 'STR', 'String'


class FieldType(DatentoolModelMixin, NamedModel, models.Model):
    """a generic field type"""
    ftype = models.CharField(max_length=3, choices=FieldTypes.choices)
    name = models.TextField()

    def validate_datatype(self, data) -> bool:
        """validate the datatype of the given data"""
        if self.ftype == FieldTypes.NUMBER:
            return isinstance(data, (int, float))
        if self.ftype == FieldTypes.STRING:
            return isinstance(data, (str, bytes))
        if self.ftype == FieldTypes.CLASSIFICATION:
            return data in self.fclass_set.values_list('value', flat=True)



class FClass(DatentoolModelMixin, models.Model):
    """a class in a classification"""
    ftype = models.ForeignKey(FieldType, on_delete=PROTECT_CASCADE)
    order = models.IntegerField()
    value = models.TextField()

    def __str__(self) -> str:
        return (f'{self.__class__.__name__}: {self.ftype.name}: '
                f'{self.order} - {self.value}')


class AreaField(DatentoolModelMixin, models.Model):
    """a field of an Area"""
    name = models.TextField()
    area_level = models.ForeignKey(AreaLevel, on_delete=PROTECT_CASCADE)
    field_type = models.ForeignKey(FieldType, on_delete=PROTECT_CASCADE)
    is_label = models.BooleanField(default=False)

    class Meta:
        unique_together = [['area_level', 'name']]


class FieldAttribute(DatentoolModelMixin, NamedModel, models.Model):
    """a value of an Area"""
    field = models.ForeignKey(AreaField, on_delete=PROTECT_CASCADE)
    str_value = models.TextField(null=True)
    num_value = models.FloatField(null=True)
    class_value = models.ForeignKey(FClass, null=True, on_delete=PROTECT_CASCADE)

    class Meta:
        abstract = True

    @property
    def value(self):
        """represent the the Attribute-instance depending on the field_type"""
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
                fclass = FClass.objects.get(ftype=self,
                                            value=data)
            except FClass.DoesNotExist:
                raise ValueError(f'{data} for field {self} is no valid value')
            self.class_value = fclass

    def __repr__(self) -> str:
        return f'{self.field.name}:{self.value}'

    def __str__(self) -> str:
        return f'{self.__class__.__name__}: {self.field.name}:{self.value}'


class AreaAttribute(FieldAttribute):
    area = models.ForeignKey(Area, on_delete=models.CASCADE)

    class Meta:
        unique_together = [['area', 'field']]
