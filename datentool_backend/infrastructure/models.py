from django.db import models
from django.contrib.gis.db import models as gis_models
from datentool_backend.base import NamedModel, JsonAttributes
from datentool_backend.user.models import Profile, Scenario
from datentool_backend.area.models import InternalWFSLayer
from datentool_backend.utils.protect_cascade import PROTECT_CASCADE
from datentool_backend.base import NamedModel, DatentoolModelMixin


class Infrastructure(DatentoolModelMixin, NamedModel, models.Model):
    '''
    Infrastructure that provide services
    '''
    name = models.TextField()
    description = models.TextField(blank=True)
    editable_by = models.ManyToManyField(
        Profile, related_name='infrastructure_editable_by', blank=True)
    accessible_by = models.ManyToManyField(
        Profile, related_name='infrastructure_accessible_by', blank=True)
    # sensitive_data
    layer = models.OneToOneField(InternalWFSLayer, on_delete=PROTECT_CASCADE)


class Service(DatentoolModelMixin, NamedModel, models.Model):
    '''
    A Service provided by an infrastructure
    '''
    name = models.TextField()
    quota_type = models.TextField()
    description = models.TextField()
    infrastructure = models.ForeignKey(Infrastructure,
                                       on_delete=PROTECT_CASCADE)
    editable_by = models.ManyToManyField(Profile,
                                         related_name='service_editable_by',
                                         blank=True)
    capacity_singular_unit = models.TextField()
    capacity_plural_unit = models.TextField()
    has_capacity = models.BooleanField()
    demand_singular_unit = models.TextField()
    demand_plural_unit = models.TextField()


class Place(DatentoolModelMixin, JsonAttributes, NamedModel, models.Model):
    """location of an infrastructure"""
    name = models.TextField()
    infrastructure = models.ForeignKey(Infrastructure,
                                       on_delete=PROTECT_CASCADE)
    geom = gis_models.PointField(geography=True)
    attributes = models.JSONField()

    def __str__(self) -> str:
        return (f'{self.__class__.__name__} ({self.infrastructure.name}): '
                f'{self.name}')


class ScenarioPlace(Place):
    scenario = models.ForeignKey(Scenario, on_delete=PROTECT_CASCADE)
    status_quo = models.ForeignKey(Place, null=True,
                                   related_name='scenario_places',
                                   on_delete=PROTECT_CASCADE)


class Capacity(DatentoolModelMixin, models.Model):
    """Capacity of an infrastructure for a service"""
    place = models.ForeignKey(Place, on_delete=PROTECT_CASCADE)
    service = models.ForeignKey(Service, on_delete=PROTECT_CASCADE)
    capacity = models.FloatField()
    from_year = models.IntegerField()


class ScenarioCapacity(Capacity):
    scenario = models.ForeignKey(Scenario, on_delete=PROTECT_CASCADE)
    status_quo = models.ForeignKey(Capacity, null=True,
                                   related_name='scenario_capacities',
                                   on_delete=PROTECT_CASCADE)


class FieldTypes(models.TextChoices):
    """enum for field types"""
    CLASSIFICATION = 'CLA', 'Classification'
    NUMBER = 'NUM', 'Number'
    STRING = 'STR', 'String'


class FieldType(DatentoolModelMixin, NamedModel, models.Model):
    """a generic field type"""
    field_type = models.CharField(max_length=3, choices=FieldTypes.choices)
    name = models.TextField()


class FClass(models.Model):
    """a class in a classification"""
    classification = models.ForeignKey(FieldType, on_delete=PROTECT_CASCADE)
    order = models.IntegerField()
    value = models.TextField()

    def __str__(self) -> str:
        return (f'{self.__class__.__name__}: {self.classification.name}: '
                f'{self.order} - {self.value}')


class PlaceField(models.Model):
    """a field of a place"""
    attribute = models.TextField()
    unit = models.TextField()
    infrastructure = models.ForeignKey(Infrastructure, on_delete=PROTECT_CASCADE)
    field_type = models.ForeignKey(FieldType, on_delete=PROTECT_CASCADE)

    def __str__(self) -> str:
        return f'{self.__class__.__name__}: {self.attribute}'

