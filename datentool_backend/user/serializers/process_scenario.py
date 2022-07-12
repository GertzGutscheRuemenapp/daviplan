from rest_framework import serializers
from typing import Dict
from collections import OrderedDict

from datentool_backend.user.models.process import (Scenario,
                                                   ScenarioMode,
                                                   ScenarioService,
                                                   PlanningProcess)
from datentool_backend.modes.models import Mode, ModeVariant


class ScenarioModeSerializer(serializers.ModelSerializer):
    mode = serializers.IntegerField(source='variant.mode')
    class Meta:
        model = ScenarioMode
        fields = ('variant', 'mode')

    def to_internal_value(self, data):
        mode = data.pop('mode', None)
        variant = data.pop('variant')
        ret = OrderedDict({
            'variant': ModeVariant.objects.get(id=variant),
            'mode': Mode(mode)
        })
        return ret


class ScenarioDemandRateSetSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScenarioService
        fields = ('demandrateset', 'service')


class ScenarioSerializer(serializers.ModelSerializer):
    mode_variants = ScenarioModeSerializer(
        many=True, source='scenariomode_set', required=False)
    demandrate_sets = ScenarioDemandRateSetSerializer(
        many=True, source='scenarioservice_set', required=False)

    class Meta:
        model = Scenario
        fields = ('id', 'name', 'planning_process', 'prognosis',
                  'mode_variants', 'demandrate_sets')
        extra_kwargs = {'prognosis': {'required': False}}

    #def get_demandratesets(self, obj) -> Dict[int, int]:
        #sets = obj.scenarioservice_set
        #return dict(sets.values_list('demandrateset__service', 'demandrateset'))

    #def validate(self, data):
        #foo = data.pop('demandrate_sets', None)
        ## Do what you want with your value
        #return super().validate(data)

    #def to_representation(self, obj):
        #data = super().to_representation(obj)
        #sets = obj.scenarioservice_set

        #data['demandrate_sets'] = [
            #{'service': drs.demandrateset.service.id,
             #'set': drs.demandrateset.id} for drs in sets.all()]
        #return data

    def update(self, instance, validated_data):
        mode_set = validated_data.pop('scenariomode_set', [])
        service_set = validated_data.pop('scenarioservice_set', [])
        super().update(instance, validated_data)

        for ms in mode_set:
            mode = ms['mode']
            variant = ms['variant']
            # variant for specific mode is intentionally set to None
            # (=> remove old one)
            if mode and not variant:
                ScenarioMode.objects.filter(
                    scenario=instance, variant__mode=mode).delete()
            else:
                try:
                    sm = ScenarioMode.objects.get(
                        scenario=instance, variant__mode=mode)
                    sm.variant = variant
                    sm.save()
                except ScenarioMode.DoesNotExist:
                    sm = ScenarioMode.objects.create(
                        scenario=instance, variant=variant)

        for sset in service_set:
            demandrate_set = sset['demandrateset']
            service = sset['service']
            # demandrate set for specific service is intentionally set to None
            # (=> remove old one)
            if service and not demandrate_set:
                ScenarioService.objects.filter(
                    scenario=instance, service=service).delete()
            else:
                try:
                    scs = ScenarioService.objects.get(
                        scenario=instance, service=service)
                    scs.demandrateset = demandrate_set
                    scs.save()
                except ScenarioService.DoesNotExist:
                    ScenarioService.objects.create(
                        scenario=instance,
                        service=service,
                        demandrateset=demandrate_set)
        return instance

    def create(self, validated_data):
        mode_set = validated_data.pop('scenariomode_set', [])
        service_set = validated_data.pop('scenarioservice_set', [])
        instance = super().create(validated_data)
        for mode in mode_set:
            sm = ScenarioMode.objects.create(
                scenario=instance, variant=mode['variant'])
        for service in service_set:
            ScenarioService.objects.create(scenario=instance,
                                           service=service['service'],
                                           demandrateset=service['demandrateset'])
        return instance


class PlanningProcessSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlanningProcess
        fields = ('id', 'name', 'owner', 'users', 'allow_shared_change',
                  'description')
        read_only_fields = ('owner', )

    def create(self, validated_data):
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            owner = request.user.profile
            validated_data['owner'] = owner
            return super().create(validated_data)
        else:
            raise serializers.ValidationError('user could not be determined')
