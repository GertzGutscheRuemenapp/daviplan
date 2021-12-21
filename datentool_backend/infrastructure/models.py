from django.db import models
from django.contrib.gis.db import models as gis_models
from datentool_backend.base import NamedModel, JsonAttributes
from datentool_backend.user.models import Profile, Scenario
from datentool_backend.area.models import InternalWFSLayer, MapSymbol


class Infrastructure(NamedModel, models.Model):
    '''
    Infrastructure that provide services
    '''
    name = models.TextField()
    description = models.TextField()
    editable_by = models.ManyToManyField(
        Profile, related_name='infrastructure_editable_by', blank=True)
    accessible_by = models.ManyToManyField(
        Profile, related_name='infrastructure_accessible_by', blank=True)
    # sensitive_data
    layer = models.ForeignKey(InternalWFSLayer, on_delete=models.RESTRICT)
    symbol = models.ForeignKey(MapSymbol, on_delete=models.RESTRICT)


class Service(NamedModel, models.Model):
    '''
    A Service provided by an infrastructure
    '''
    name = models.TextField()
    quota_type = models.TextField()
    description = models.TextField()
    infrastructure = models.ForeignKey(Infrastructure, on_delete=models.RESTRICT)
    editable_by = models.ManyToManyField(Profile,
                                         related_name='service_editable_by',
                                         blank=True)
    capacity_singular_unit = models.TextField()
    capacity_plural_unit = models.TextField()
    has_capacity = models.BooleanField()
    demand_singular_unit = models.TextField()
    demand_plural_unit = models.TextField()


class Place(JsonAttributes, NamedModel, models.Model):
    """location of an infrastructure"""
    name = models.TextField()
    infrastructure = models.ForeignKey(Infrastructure, on_delete=models.RESTRICT)
    geom = gis_models.PointField(geography=True)
    attributes = models.JSONField()

    def __str__(self) -> str:
        return f'{self.__class__.__name__} ({self.infrastructure.name}): {self.name}'


class ScenarioPlace(Place):
    scenario = models.ForeignKey(Scenario, on_delete=models.RESTRICT)
    status_quo = models.ForeignKey(Place, null=True,
                                   related_name='scenario_places',
                                   on_delete=models.RESTRICT)


class Capacity(models.Model):
    """Capacity of an infrastructure for a service"""
    place = models.ForeignKey(Place, on_delete=models.RESTRICT)
    service = models.ForeignKey(Service, on_delete=models.RESTRICT)
    capacity = models.FloatField()
    from_year = models.IntegerField()


class ScenarioCapacity(Capacity):
    scenario = models.ForeignKey(Scenario, on_delete=models.RESTRICT)
    status_quo = models.ForeignKey(Capacity, null=True,
                                   related_name='scenario_capacities',
                                   on_delete=models.RESTRICT)


class FieldTypes(models.TextChoices):
    """enum for field types"""
    CLASSIFICATION = 'CLA', 'Classification'
    NUMBER = 'NUM', 'Number'
    STRING = 'STR', 'String'


class FieldType(NamedModel, models.Model):
    """a generic field type"""
    field_type = models.CharField(max_length=3, choices=FieldTypes.choices)
    name = models.TextField()


class FClass(models.Model):
    """a class in a classification"""
    classification = models.ForeignKey(FieldType, on_delete=models.RESTRICT)
    order = models.IntegerField()
    value = models.TextField()

    def __str__(self) -> str:
        return f'{self.__class__.__name__}: {self.classification.name}: {self.order} - {self.value}'


class PlaceField(models.Model):
    """a field of a place"""
    attribute = models.TextField()
    unit = models.TextField()
    infrastructure = models.ForeignKey(Infrastructure, on_delete=models.RESTRICT)
    field_type = models.ForeignKey(FieldType, on_delete=models.RESTRICT)

    def __str__(self) -> str:
        return f'{self.__class__.__name__}: {self.attribute}'

