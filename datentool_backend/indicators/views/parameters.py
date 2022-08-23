from drf_spectacular.utils import inline_serializer
from rest_framework import serializers

from datentool_backend.area.models import AreaLevel, Area
from datentool_backend.user.models.process import Scenario
from datentool_backend.population.models import Prognosis
from datentool_backend.infrastructure.models.infrastructures import Service
from datentool_backend.demand.models import AgeGroup, Gender
from datentool_backend.modes.models import Mode


arealevel_year_service_scenario_serializer = inline_serializer(
    name='AreaLevelYearServiceScenarioSerializer',
    fields={
        'area_level': serializers.PrimaryKeyRelatedField(
            queryset=AreaLevel.objects.all(),
            required=True, help_text='area_level_id'),
        'year': serializers.IntegerField(required=False,
                                         help_text='Jahr (z.B. 2010)'),
        'services': serializers.ListField(child=serializers.PrimaryKeyRelatedField(
            queryset=Service.objects.all()),
            required=True, help_text='service ids'),
        'scenario':  serializers.PrimaryKeyRelatedField(
            queryset=Scenario.objects.all(),
            required=False, help_text='scenario_id'),
    }
)

area_agegroup_gender_prognosis_year_fields={
    'areas': serializers.ListField(child=serializers.PrimaryKeyRelatedField(
        queryset=Area.objects.all()),
                                  required=False,
                                  help_text='area_ids'),
    'age_groups': serializers.ListField(child=serializers.PrimaryKeyRelatedField(
        queryset=AgeGroup.objects.all()
    ),
                                       required=False,
                                       help_text='age_group_ids'),
    'genders': serializers.ListField(child=serializers.PrimaryKeyRelatedField(
        queryset=Gender.objects.all()
    ),
                                     required=False,
                                     help_text='gender_ids'),
    'prognosis':  serializers.PrimaryKeyRelatedField(
        queryset=Prognosis.objects.all(),
        required=False, help_text='prognosis_id'),
    'year': serializers.IntegerField(required=False,
                                     help_text='Jahr (z.B. 2010)'),
}

arealevel_area_agegroup_gender_prognosis_year_fields = {
    'area_level': serializers.PrimaryKeyRelatedField(
        queryset=AreaLevel.objects.all(),
        required=True, help_text='area_level_id'),
}

arealevel_area_agegroup_gender_prognosis_year_fields.update(
    area_agegroup_gender_prognosis_year_fields)


mode_year_service_scenario_serializer = inline_serializer(
    name='ModeYearServiceScenarioSerializer',
    fields={
        'year': serializers.IntegerField(required=False,
                                         help_text='Jahr (z.B. 2010)'),
        'services': serializers.ListField(child=serializers.PrimaryKeyRelatedField(
            queryset=Service.objects.all()),
            required=True, help_text='service ids'),
        'scenario': serializers.PrimaryKeyRelatedField(
            queryset=Scenario.objects.all(),
            required=False, help_text='scenario_id'),
        'mode': serializers.IntegerField(),
    },
)
