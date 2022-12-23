from django.db import models
from django.contrib.auth.models import User

from datentool_backend.base import NamedModel, DatentoolModelMixin
from datentool_backend.utils.protect_cascade import PROTECT_CASCADE
from datentool_backend.population.models import Prognosis
from datentool_backend.demand.models import DemandRateSet
from datentool_backend.modes.models import ModeVariant, Mode
from datentool_backend.user.models import Profile
from datentool_backend.infrastructure.models import (Service, Infrastructure)


class PlanningProcess(DatentoolModelMixin, NamedModel, models.Model):
    '''
    Basic Project Information
    '''
    name = models.TextField()
    description = models.TextField(default='', blank=True)
    owner = models.ForeignKey(Profile, on_delete=models.CASCADE)
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
            # set default prognosis
            try:
                self.prognosis = Prognosis.objects.get(is_default=True)
            except Prognosis.DoesNotExist:
                pass

            # set default DemandRateSets for Services in Scenario
            for default_set in DemandRateSet.objects.filter(is_default=True):
                ScenarioService.objects.create(scenario=self,
                                               service=default_set.service,
                                               demandrateset=default_set)

            # create default scenario mode-variants
            for mode in [Mode.WALK, Mode.BIKE, Mode.CAR, Mode.TRANSIT]:
                try:
                    variant = ModeVariant.objects.get(mode=mode,
                                                      is_default=True)
                except ModeVariant.DoesNotExist:
                    try:
                        variant = ModeVariant.objects.get(mode=mode,
                                                      network__is_default=True)
                    except ModeVariant.DoesNotExist:
                        continue
                ScenarioMode.objects.create(scenario=self,
                                            variant=variant)

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
    variant = models.ForeignKey(ModeVariant, on_delete=models.CASCADE)

    def save(self, *args, **kwargs):
        # only one ScenarioModeVariant per Scenario and Mode allowed
        other_sm = ScenarioMode.objects\
            .filter(scenario=self.scenario,
                    variant__mode=self.variant.mode)\
            .exclude(pk=self.pk)
        other_sm.delete()
        super().save(*args, **kwargs)

class ScenarioService(models.Model):
    scenario = models.ForeignKey(Scenario, on_delete=models.CASCADE)
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    demandrateset = models.ForeignKey(DemandRateSet, on_delete=PROTECT_CASCADE)
