from django.db import models
from django.contrib.auth.models import User

from datentool_backend.base import NamedModel, DatentoolModelMixin
from datentool_backend.utils.protect_cascade import PROTECT_CASCADE
from datentool_backend.population.models import Prognosis
from datentool_backend.demand.models import DemandRateSet
from datentool_backend.modes.models import ModeVariant, Network
from datentool_backend.infrastructure.models.infrastructures import (
    Service, Infrastructure)
from .profile import Profile


class PlanningProcess(DatentoolModelMixin, NamedModel, models.Model):
    '''
    Basic Project Information
    '''
    name = models.TextField()
    description = models.TextField(default='', blank=True)
    owner = models.ForeignKey(Profile, on_delete=models.RESTRICT)
    users = models.ManyToManyField(Profile, related_name='shared_with_users',
                                   blank=True)
    infrastructures = models.ManyToManyField(
        Infrastructure, related_name='processes', blank=True)
    allow_shared_change = models.BooleanField()


class Scenario(DatentoolModelMixin, NamedModel, models.Model):
    """BULE-Scenario"""
    name = models.TextField()
    planning_process = models.ForeignKey(PlanningProcess,
                                         on_delete=models.CASCADE)
    prognosis = models.ForeignKey(Prognosis, on_delete=models.SET_NULL,
                                  null=True)
    demandratesets = models.ManyToManyField(DemandRateSet,
                                            related_name='scenario_service',
                                            blank=True,
                                            through='ScenarioService')

    def save(self, **kwargs):
        is_created = self.pk == None
        super().save(**kwargs)
        if is_created:
            try:
                self.prognosis = Prognosis.objects.get(is_default=True)
            except Prognosis.DoesNotExist:
                pass
            for default_set in DemandRateSet.objects.filter(is_default=True):
                ScenarioService.objects.create(scenario=self,
                                               service=default_set.service,
                                               demandrateset=default_set)
            try:
                default_network = Network.objects.get(is_default=True)
                for default_mode in ModeVariant.objects.filter(
                    is_default=True, network=default_network):
                    ScenarioMode.objects.create(scenario=self,
                                                variant=default_mode)
            except Network.DoesNotExist:
                pass

    def has_write_permission(self, user: User):
        owner_is_user = user.profile == self.planning_process.owner
        user_in_users = user.profile in self.planning_process.users.all()
        allow_shared_change = self.planning_process.allow_shared_change
        return owner_is_user or (allow_shared_change and user_in_users)

    def has_read_permission(self, user: User):
        owner_is_user = user.profile == self.planning_process.owner
        user_in_users = user.profile in self.planning_process.users.all()
        return owner_is_user or user_in_users


class ScenarioMode(models.Model):
    scenario = models.ForeignKey(Scenario, on_delete=models.CASCADE)
    variant = models.ForeignKey(ModeVariant, on_delete=PROTECT_CASCADE)


class ScenarioService(models.Model):
    scenario = models.ForeignKey(Scenario, on_delete=models.CASCADE)
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    demandrateset = models.ForeignKey(DemandRateSet, on_delete=PROTECT_CASCADE)