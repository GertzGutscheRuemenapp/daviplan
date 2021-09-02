from faker import Factory
from faker.generator import Generator
import factory
from factory.django import DjangoModelFactory
from .models import (Years, Raster, RasterCell)

faker: Generator = Factory.create()


class YearFactory(DjangoModelFactory):
    class Meta:
        model = Years

    year = faker.year()


class RasterFactory(DjangoModelFactory):
    class Meta:
        model = Raster
        django_get_or_create = ('year', )

    name = faker.word()
    year = factory.SubFactory(YearFactory)


class RasterCellFactory(DjangoModelFactory):
    class Meta:
        model = RasterCell
        django_get_or_create = ('raster', )

    raster = factory.SubFactory(RasterFactory)
    cellcode = faker.pystr_format(string_format=f'100mN####E####')
    value = faker.pyfloat(max_value=100)