from typing import List

from django.db import models
from django.db.models.signals import post_save
from django.db.models import Q
from django.contrib.gis.db import models as gis_models
from sql_util.utils import Exists

from datentool_backend.base import (NamedModel,
                                    DatentoolModelMixin,
                                    )
from datentool_backend.utils.protect_cascade import PROTECT_CASCADE
from datentool_backend.utils.copy_postgres import DirectCopyManager

from datentool_backend.area.models import (FieldType, FieldTypes,
                                           FieldAttribute)
from datentool_backend.user.models.process import Scenario
from .infrastructures import Infrastructure, Service, PlaceField


class Place(DatentoolModelMixin, NamedModel, models.Model):
    """location of an infrastructure"""
    objects = models.Manager()
    copymanager = DirectCopyManager()

    name = models.TextField()
    infrastructure = models.ForeignKey(Infrastructure,
                                       on_delete=PROTECT_CASCADE)
    service_capacity = models.ManyToManyField(Service, related_name='place_services',
                                              blank=True, through='Capacity')
    geom = gis_models.PointField(srid=3857)
    scenario = models.ForeignKey(Scenario, on_delete=PROTECT_CASCADE, null=True)

    def __str__(self) -> str:
        return (f'{self.__class__.__name__} ({self.infrastructure.name}): '
                f'{self.name}')

    @property
    def attributes(self):
        return self.placeattribute_set

    @property
    def label(self):
        """The area label retrieved from the attributes"""
        try:
            label_attr = self.attributes.get(field__is_label=True)
        except PlaceAttribute.DoesNotExist:
            return ''
        return label_attr.value

    @attributes.setter
    def attributes(self, attr_dict: dict):
        if not self.pk:
            self._attr_dict = attr_dict
            return
        pa = PlaceAttribute.objects.filter(place=self)
        pa.delete()
        for field_name, value in attr_dict.items():
            try:
                field = PlaceField.objects.get(infrastructure=self.infrastructure,
                                              name=field_name)
            except PlaceField.DoesNotExist:
                if isinstance(value, (int, float)):
                    ftype = FieldTypes.NUMBER
                else:
                    ftype = FieldTypes.STRING
                field_type, created = FieldType.objects.get_or_create(ftype=ftype,
                                                                      name=ftype.value)
                field = PlaceField.objects.create(infrastructure=self.infrastructure,
                                                  name=field_name,
                                                  field_type=field_type,
                                                  )
            pa = PlaceAttribute(place=self, field=field)
            pa.value = value
            pa.save()

    @staticmethod
    def post_create(sender, instance, created, *args, **kwargs):
        if not created:
            return
        if hasattr(instance, '_attr_dict'):
            instance.attributes = instance._attr_dict


post_save.connect(Place.post_create, sender=Place)


class PlaceAttribute(FieldAttribute):
    objects = models.Manager()
    copymanager = DirectCopyManager()

    place = models.ForeignKey(Place, on_delete=models.CASCADE)
    field = models.ForeignKey(PlaceField, on_delete=PROTECT_CASCADE)

    class Meta:
        unique_together = [['place', 'field']]


class Capacity(DatentoolModelMixin, models.Model):
    """Capacity of an infrastructure for a service"""
    objects = models.Manager()
    copymanager = DirectCopyManager()

    place = models.ForeignKey(Place, on_delete=PROTECT_CASCADE)
    service = models.ForeignKey(Service, on_delete=PROTECT_CASCADE)
    capacity = models.FloatField(default=1)
    from_year = models.IntegerField(default=0)
    to_year = models.IntegerField(default=99999999)
    scenario = models.ForeignKey(Scenario, on_delete=PROTECT_CASCADE, null=True)

    def __str__(self) -> str:
        place = getattr(self.place, 'pk', '_')
        service = getattr(self.service, 'pk', '_')
        scenario = getattr(self.scenario, 'pk', '_')
        return (f'{self.__class__.__name__} '
                f'(Pl{place}-Se{service}-Sc{scenario} '
                f'Y{self.from_year}-{self.to_year}): '
                f'{self.capacity}')

    class Meta:
        unique_together = ['place', 'service', 'from_year', 'scenario']

    def save(self, *args, **kwargs):
        """
        Update to_year in the last row and
        from_year in the current row before saving
        """
        last_row = Capacity.objects.filter(place=self.place,
                                     service=self.service,
                                     from_year__lt=self.from_year,
                                     scenario=self.scenario)\
            .order_by('from_year')\
            .last()
        if last_row:
            last_row.to_year = self.from_year - 1
            super(Capacity, last_row).save()

        next_row = Capacity.objects.filter(place=self.place,
                                           service=self.service,
                                           from_year__gt=self.from_year,
                                           scenario=self.scenario)\
            .order_by('from_year')\
            .first()
        if next_row:
            self.to_year = next_row.from_year - 1

        super().save(*args, **kwargs)

    @staticmethod
    def filter_queryset(queryset,
                        service_ids: List[int] = [],
                        scenario_id: int = None,
                        year: int = None):
        """filter queryset by scenario and year, if given"""
        # filter capacities by service, if this is requested
        if service_ids:
            queryset = queryset.filter(service__in=service_ids)

        if year is not None:
            # filter capacities by year
            queryset = queryset\
                .filter(from_year__lte=year)\
                .filter(to_year__gte=year)

        # if base scenario is requested, filter by base scenario (= None)
        if scenario_id is None:
            return queryset.filter(scenario=None)

        # otherwise, the scenario is requested
        # find the places, that have specific capacities
        # for this scenario defined
        scenario_filter = Q(scenario=scenario_id)
        #  if a specific services is requested,
        # filter only the places with capacities for this service
        if service_ids is None:
            scenario_filter = scenario_filter & Q(service__in=service_ids)
        # get the places that have have capacities
        # defined for the scenario (and service)
        places_with_scenario = Place.objects.filter(Exists(
            'capacity', filter=scenario_filter))
        # ... and those not
        places_without_scenario = Place.objects.exclude(Exists(
            'capacity', filter=scenario_filter))

        # get the capacities defined for the scenario,
        # and for the places wihout scenario, the capacities from the base scenario
        res_queryset = queryset\
            .filter((Q(scenario__in=scenario_id) & Q(place__in=places_with_scenario)) |
                    (Q(scenario=None) & Q(place__in=places_without_scenario))
                    )
        return res_queryset
