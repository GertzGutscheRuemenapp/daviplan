from django.db import models

from datentool_backend.base import NamedModel, DatentoolModelMixin
from datentool_backend.utils.protect_cascade import PROTECT_CASCADE
from datentool_backend.population.models import Prognosis
from datentool_backend.demand.models import DemandRateSet
from datentool_backend.modes.models import ModeVariant
from datentool_backend.infrastructure.models.infrastructures import Service
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
    allow_shared_change = models.BooleanField()


class Scenario(DatentoolModelMixin, NamedModel, models.Model):
    """BULE-Scenario"""
    name = models.TextField()
    planning_process = models.ForeignKey(PlanningProcess,
                                         on_delete=PROTECT_CASCADE)
    prognosis = models.ForeignKey(Prognosis, on_delete=PROTECT_CASCADE,
                                  null=True)
    demandratesets = models.ManyToManyField(DemandRateSet,
                                            related_name='scenario_service',
                                            blank=True,
                                            through='ScenarioService')


class ScenarioMode(models.Model):
    scenario = models.ForeignKey(Scenario, on_delete=PROTECT_CASCADE)
    variant = models.ForeignKey(ModeVariant, on_delete=PROTECT_CASCADE)


class ScenarioService(models.Model):
    scenario = models.ForeignKey(Scenario, on_delete=PROTECT_CASCADE)
    service = models.ForeignKey(Service, on_delete=PROTECT_CASCADE)
    demandrateset = models.ForeignKey(DemandRateSet, on_delete=PROTECT_CASCADE)