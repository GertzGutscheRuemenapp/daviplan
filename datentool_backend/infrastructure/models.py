from django.db import models
from django.contrib.gis.db import models as gis_models
from ..user.models import Profile
from ..area.models import InternalWFSLayer, MapSymbols


class Infrastructure(models.Model):
    '''
    Infrastructure that provide services
    '''
    name = models.TextField()
    description = models.TextField()
    editable_by = models.ManyToManyField(
        Profile, related_name='infrastructure_editable_by')
    accessible_by = models.ManyToManyField(
        Profile, related_name='infrastructure_accessible_by')
    # sensitive_data
    layer = models.ForeignKey(InternalWFSLayer, on_delete=models.RESTRICT)
    symbol = models.ForeignKey(MapSymbols, on_delete=models.RESTRICT)


class Quota(models.Model):
    """kind of capacity"""
    quota_type = models.TextField()


class Service(models.Model):
    '''
    A Service provided by an infrastructure
    '''
    name = models.TextField()
    description = models.TextField()
    infrastructure = models.ForeignKey(Infrastructure, on_delete=models.RESTRICT)
    editable_by = models.ManyToManyField(Profile, related_name='service_editable_by')
    capacity_singular_unit = models.TextField()
    capacity_plural_unit = models.TextField()
    has_capacity = models.BooleanField()
    demand_singular_unit = models.TextField()
    demand_plural_unit = models.TextField()
    quota = models.ForeignKey(Quota, on_delete=models.RESTRICT)


class Place(models.Model):
    """location of an infrastructure"""
    name = models.TextField()
    infrastructure = models.ForeignKey(Infrastructure, on_delete=models.RESTRICT)
    geom = gis_models.PointField()
    attributes = models.JSONField()


class Capacity(models.Model):
    """Capacity of an infrastructure for a service"""
    place = models.ForeignKey(Place, on_delete=models.RESTRICT)
    service = models.ForeignKey(Service, on_delete=models.RESTRICT)
    capacity = models.FloatField()
    from_year = models.IntegerField()


class FieldTypes(models.TextChoices):
    """enum for field types"""
    CLASSIFICATION = 'CLA', 'Classification'
    NUMBER = 'NUM', 'Number'
    STRING = 'STR', 'String'

class FieldType(models.Model):
    """a generic field type"""
    field_type = models.CharField(max_length=3, choices=FieldTypes.choices)
    name = models.TextField()


class FClass(models.Model):
    """a class in a classification"""
    classification = models.ForeignKey(FieldType, on_delete=models.RESTRICT)
    order = models.IntegerField(unique=True)
    value = models.TextField()


class PlaceField(models.Model):
    """a field of a place"""
    attribure = models.TextField()
    unit = models.TextField()
    infrastructure = models.ForeignKey(Infrastructure, on_delete=models.RESTRICT)
    field_type = models.ForeignKey(FieldType, on_delete=models.RESTRICT)