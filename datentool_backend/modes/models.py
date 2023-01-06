from typing import List
from django.db import models

from datentool_backend.base import (NamedModel,
                                    DatentoolModelMixin, )
from datentool_backend.infrastructure.models import Infrastructure


class Mode(models.IntegerChoices):
    WALK = 1, 'zu Fuß'
    BIKE = 2, 'Fahrrad'
    CAR = 3, 'Auto'
    TRANSIT = 4, 'ÖPNV'

MODE_SPEED = {
    Mode.WALK: 3.5,
    Mode.BIKE: 10.5,
    Mode.CAR: 25,
}

MODE_MAX_DISTANCE = {
    Mode.WALK: 4000,
    Mode.BIKE: 15000,
    Mode.CAR: 50000,
    Mode.TRANSIT: 1000,
}

MODE_ROUTERS = {
    Mode.WALK: 'foot',
    Mode.BIKE: 'bicycle',
    Mode.CAR: 'car',
}

# default maximum walk time, insdead of transit use
DEFAULT_MAX_DIRECT_WALKTIME = 15


class Network(DatentoolModelMixin, NamedModel, models.Model):
    name = models.TextField(default='', blank=True)
    is_default = models.BooleanField(default=False)
    network_file = models.FileField(null=True)

    def save(self, *args, modes2create=[Mode.WALK, Mode.BIKE, Mode.CAR], **kwargs):
        self._set_as_default()
        # create the modes for this network
        created = self.pk is None
        if created:
            variants = self._create_network_modes(modes2create)
        super().save(*args, **kwargs)
        if created:
            ModeVariant.objects.bulk_create(variants)

    def _set_as_default(self):
        """only one network can be a default"""
        if self.is_default:
            Network.objects\
                .filter(is_default=True)\
                .exclude(pk=self.pk)\
                .update(is_default=False)

    def _create_network_modes(self,
                              modes: List[Mode] =
                              [Mode.WALK, Mode.BIKE, Mode.CAR]) -> List['ModeVariant']:
        """Create the modes for the network"""
        variants = []
        for mode in modes:
            # is there is no another default variant
            is_default = not ModeVariant.objects.filter(mode=mode,
                                                        is_default=True).exists()
            variants.append(ModeVariant(network=self,
                                        mode=mode,
                                        is_default=is_default))
        return variants


class ModeVariant(DatentoolModelMixin, models.Model):
    '''
    modes
    '''
    label = models.TextField(default='', blank=True)
    network = models.ForeignKey(Network, on_delete=models.CASCADE, null=True)
    mode = models.IntegerField(choices=Mode.choices)
    cutoff_time = models.ManyToManyField(Infrastructure, through='CutOffTime')
    is_default = models.BooleanField(default=False)

    def __str__(self) -> str:
        s = f'ModeVariant {Mode(self.mode).name} - {self.label}'
        if self.is_default:
            s += ' (default)'
        return s

    def save(self, *args, **kwargs):

        # for each mode, there should be exactly one default mode
        if self.is_default:
            ModeVariant.objects.filter(
                is_default=True,
                mode=self.mode)\
                .exclude(pk=self.pk)\
                .update(is_default=False)
        else:
            other_default = ModeVariant.objects.filter(mode=self.mode,
                                                       is_default=True).exists()
            if not other_default:
                self.is_default = True

        if self.mode == Mode.TRANSIT:
            # on creation
            if self.pk is None:
                #-> look if there is already a default transit variant,
                try:
                    ModeVariant.objects.get(is_default=True, mode=Mode.TRANSIT)
                # else set this as default (so there is always a default one)
                except ModeVariant.DoesNotExist:
                    self.is_default = True
        else:
            # for non-transit-modes, if no network is defined,
            # take or create the default network
            if not self.network:
                try:
                    network = Network.objects.get(is_default=True)
                except Network.DoesNotExist:
                    # if it does not exist, the network should only create the
                    # other mode variants automatically
                    network = Network(is_default=True)
                    modes2create = [m for m in
                                       [Mode.WALK, Mode.BIKE, Mode.CAR]
                                       if m != self.mode]
                    network.save(modes2create=modes2create)
                self.network = network

        super().save(*args, **kwargs)

    def delete(self, **kwargs):
        # deleting transit variant marked as default -> mark another one
        # transit variant (so there always is one default set if there are
        # any at all)
        if self.mode == Mode.TRANSIT and self.is_default:
            new_default = ModeVariant.objects.filter(
                mode=Mode.TRANSIT).exclude(id=self.id).first()
            if new_default:
                new_default.is_default = True
                new_default.save()
        return super().delete(**kwargs)

    def get_n_rels(self, matname: str):
        """get the number of relations for the specified matrix"""
        rel = f'n_rels_{matname}'
        variant_statistic, created = ModeVariantStatistic.objects\
            .get_or_create(variant=variant)
        cnt = getattr(variant_statistic, rel)
        # if statistic does not exist yet, calculate it from the matrix
        if created:
            cnt=MatrixCellPlace.objects.filter(variant=variant).count()
            setattr(variant_statistic, rel, cnt)
            variant_statistic.save()
        return cnt


class ModeVariantStatistic(models.Model):
    variant = models.OneToOneField(ModeVariant, on_delete=models.CASCADE)
    n_rels_place_cell = models.IntegerField(null=True)
    n_rels_place_stop = models.IntegerField(null=True)
    n_rels_stop_cell = models.IntegerField(null=True)
    n_rels_stop_stop = models.IntegerField(null=True)


class CutOffTime(models.Model):
    mode_variant = models.ForeignKey(ModeVariant, on_delete=models.CASCADE)
    infrastructure = models.ForeignKey(Infrastructure, on_delete=models.CASCADE)
    minutes = models.FloatField()


def get_default_access_variant():
    variant, created = ModeVariant.objects.get_or_create(mode=Mode.WALK,
                                                         is_default=True)
    return variant.pk


def get_default_transit_variant():
    variant, created = ModeVariant.objects.get_or_create(mode=Mode.TRANSIT,
                                                         is_default=True)
    return variant.pk
