from rest_framework import serializers


class MessageSerializer(serializers.Serializer):
    message = serializers.CharField()


use_intersected_data = serializers.BooleanField(
        default=True,
        help_text='''use precalculated rastercells''')


drop_constraints = serializers.BooleanField(
    default=False,
    label='temporarily delete constraints and indices',
    help_text='Set to False in unittests')


area_level = serializers.IntegerField(
        required=False,
        help_text='''if a specific area_level_id is provided,
        take this one instead of the areas of the population''')
