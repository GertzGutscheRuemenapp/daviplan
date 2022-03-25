from rest_framework import serializers

from datentool_backend.infrastructure.models import (Scenario,
                                                     ScenarioMode,
                                                     ScenarioService,
                                                     )


class ScenarioModeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScenarioMode
        fields = ('variant',)


class ScenarioDemandRateSetSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScenarioService
        fields = ('demandrateset', )


class ScenarioSerializer(serializers.ModelSerializer):
    modevariants = ScenarioModeSerializer(
        many=True, source='scenariomode_set', required=False)
    demandratesets = ScenarioDemandRateSetSerializer(
        many=True, source='scenarioservice_set', required=False)

    class Meta:
        model = Scenario
        fields = ('id', 'name', 'planning_process', 'prognosis',
                  'modevariants', 'demandratesets')
        extra_kwargs = {'prognosis': {'required': False}}

    def update(self, instance, validated_data):
        mode_set = validated_data.pop('scenariomode_set', [])
        service_set = validated_data.pop('scenarioservice_set', [])
        super().update(instance, validated_data)

        for mode in mode_set:
            try:
                sm = ScenarioMode.objects.get(
                    scenario=instance, variant__mode=mode['variant'].mode)
                sm.variant = mode['variant']
                sm.save()
            except ScenarioMode.DoesNotExist:
                sm = ScenarioMode.objects.create(
                    scenario=instance, variant=mode['variant'])

        for service in service_set:
            try:
                scs = ScenarioService.objects.get(
                    scenario=instance, service=service['demandrateset'].service)
                scs.demandrateset = service['demandrateset']
                scs.save()
            except ScenarioService.DoesNotExist:
                ScenarioService.objects.create(scenario=instance,
                                               service=service['demandrateset'].service,
                                               demandrateset=service['demandrateset'])

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
                                           service=service['demandrateset'].service,
                                           demandrateset=service['demandrateset'])
        return instance

