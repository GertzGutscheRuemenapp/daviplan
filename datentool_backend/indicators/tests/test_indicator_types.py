from django.test import TestCase
from test_plus import APITestCase
from datentool_backend.api_test import BasicModelReadTest
from datentool_backend.area.tests import TestAPIMixin


from ..factories import (RouterFactory, IndicatorFactory, MatrixCellPlaceFactory,
                         MatrixCellStopFactory, MatrixPlaceStopFactory,
                         MatrixStopStopFactory)

from ..models import (IndicatorType, IndicatorTypeField,)
from ..compute import (NumberOfLocations,
                       TotalCapacityInArea,
                       register_indicator_class,
                       ComputeIndicator)

from datentool_backend.infrastructure.models import FieldTypes


class TestIndicator(TestCase):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        register_indicator_class()(DummyIndicator)
        IndicatorType._update_indicators_types()

    @classmethod
    def tearDownClass(cls):
        # unregister the dummy class
        del IndicatorType._indicator_classes[DummyIndicator.__name__]
        super().tearDownClass()

    def test_router(self):
        RouterFactory()

    def test_indicator(self):
        num_locs = IndicatorType.objects.get(
            classname=NumberOfLocations.__name__)
        IndicatorFactory(indicator_type=num_locs)

    def test_matrix_cell_place(self):
        MatrixCellPlaceFactory()

    def test_matrix_cell_stop(self):
        MatrixCellStopFactory()

    def test_matrix_place_stop(self):
        MatrixPlaceStopFactory()

    def test_matrix_stop_stop(self):
        MatrixStopStopFactory()

    def test_indicator_types(self):
        """test if the indicator types are registred"""
        indicator = NumberOfLocations(query_params={})
        str(indicator)

        indicator_types = IndicatorType.objects.all()

        # add an unknown indicator
        IndicatorFactory(indicator_type__classname='Unknown')
        assert set(['Unknown',
                    DummyIndicator.__name__,
                    NumberOfLocations.__name__,
                    TotalCapacityInArea.__name__,
                    ])\
               .issubset(set(indicator_types.values_list('classname', flat=True)))

        # delete an indicator_type
        IndicatorType.objects.get(classname=NumberOfLocations.__name__).delete()

        #  change parameters of other indicators
        dummy_indicator = IndicatorType.objects.get(classname=DummyIndicator.__name__)
        dummy_fields = IndicatorTypeField.objects.filter(
            indicator_type__classname=DummyIndicator.__name__)
        self.assertEquals(len(dummy_fields), 2)

        dummy_indicator.name = 'NewName'
        dummy_indicator.save()
        dummy_fields[0].delete()
        self.assertEqual(dummy_fields[1].field_type.field_type,
                         DummyIndicator.parameters[dummy_fields[1].field_type.name])

        # change fieldtype
        f1 = dummy_fields[1]
        f1.field_type.field_type = FieldTypes.CLASSIFICATION
        f1.field_type.save()

        # add fields
        IndicatorTypeField.objects.create(indicator_type=dummy_indicator,
                                          field_type=f1.field_type,
                                          label='F1')
        IndicatorTypeField.objects.create(indicator_type=dummy_indicator,
                                          field_type=f1.field_type,
                                          label='F2')

        indicators_values_list = indicator_types.values_list('classname', flat=True)
        assert set(['Unknown',
                    DummyIndicator.__name__,
                    TotalCapacityInArea.__name__,
                    ]).issubset(set(indicators_values_list))

        assert NumberOfLocations.__name__ not in indicators_values_list

        # reset the indicators
        IndicatorType._update_indicators_types()
        assert set([DummyIndicator.__name__,
                    NumberOfLocations.__name__,
                    TotalCapacityInArea.__name__,
                    ])\
               .issubset(set(indicator_types.values_list('classname', flat=True)))


        dummy_indicator = IndicatorType.objects.get(classname=DummyIndicator.__name__)
        dummy_fields = IndicatorTypeField.objects.filter(
            indicator_type__classname=DummyIndicator.__name__)
        self.assertEquals(len(dummy_fields), 2)
        self.assertEquals(dummy_indicator.name, DummyIndicator.label)


class DummyIndicator(ComputeIndicator):
    label = 'TE'
    description = 'Random Indicator'
    parameters = {'Max_Value': FieldTypes.NUMBER, 'TextField': FieldTypes.STRING, }

    def compute(self):
        """"""


class TestIndicatorTypeAPI(TestAPIMixin, BasicModelReadTest, APITestCase):
    """Test to get an area indicator"""
    url_key = "indicatortypes"

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        register_indicator_class()(DummyIndicator)
        IndicatorType._update_indicators_types()
        cls.obj = IndicatorType.objects.get(classname=DummyIndicator.__name__)

    @classmethod
    def tearDownClass(cls):
        # unregister the dummy class
        del IndicatorType._indicator_classes[DummyIndicator.__name__]
        super().tearDownClass()
