from drf_spectacular.utils import OpenApiParameter


area_level_param = OpenApiParameter(name='area_level', type=int,
                                    description='Area Level PKey')
areas_param = OpenApiParameter(name='area',
                               type={'type': 'array', 'items': {'type': 'integer',},},
                               description='Area PKeys',
                               required=False)
prognosis_param = OpenApiParameter(name='prognosis', type=int, required=False,
                                   description='Prognosis PKey')
scenario_param = OpenApiParameter(name='scenario', type=int, required=False,
                                   description='Scenario PKey')
year_param = OpenApiParameter(name='year', type=int, required=False, description='Jahr als Datum (z.B. 2027)')
genders_param = OpenApiParameter(name='gender',
                                 type={'type': 'array', 'items': {'type': 'integer',},},
                                 description='Gender PKeys',
                                 required=False)
age_groups_param = OpenApiParameter(name='age_group',
                                    type={'type': 'array', 'items': {'type': 'integer',},},
                                    description='Age Group PKeys',
                                    required=False)
services_param = OpenApiParameter(name='service',
                                  type={'type': 'array', 'items': {'type': 'integer',},},
                                  description='Service PKeys',
                                  required=False)
place_param = OpenApiParameter(name='place', type=int,
                               description='Place PKey')
loc_x_param = OpenApiParameter(name='cell', type=float,
                               description='x-coordinate (WGS 84)')
loc_y_param = OpenApiParameter(name='cell', type=float,
                               description='y-coordinate (WGS 84)')