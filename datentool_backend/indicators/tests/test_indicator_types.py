from django.test import TestCase

from datentool_backend.indicators.factories import (
    RouterFactory, MatrixCellPlaceFactory,
    MatrixCellStopFactory, MatrixPlaceStopFactory,
    MatrixStopStopFactory)

from datentool_backend.indicators.compute import (
    register_indicator, ServiceIndicator)

from datentool_backend.infrastructure.models.places import FieldTypes


class TestIndicator(TestCase):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        register_indicator()(DummyIndicator)

    def test_router(self):
        RouterFactory()

    def test_matrix_cell_place(self):
        MatrixCellPlaceFactory()

    def test_matrix_cell_stop(self):
        MatrixCellStopFactory()

    def test_matrix_place_stop(self):
        MatrixPlaceStopFactory()

    def test_matrix_stop_stop(self):
        MatrixStopStopFactory()

    #def test_indicator_types(self):
        #"""test if the indicator types are registred"""
        #indicator = NumberOfLocations(query_params={})
        #str(indicator)

        #indicator_types = IndicatorType.objects.all()

        ## add an unknown indicator
        #IndicatorFactory(indicator_type__classname='Unknown')
        #assert set(['Unknown',
                    #DummyIndicator.__name__,
                    #NumberOfLocations.__name__,
                    #TotalCapacityInArea.__name__,
                    #])\
               #.issubset(set(indicator_types.values_list('classname', flat=True)))

        ## delete an indicator_type
        #IndicatorType.objects.get(classname=NumberOfLocations.__name__).delete()

        ##  change parameters of other indicators
        #dummy_indicator = IndicatorType.objects.get(classname=DummyIndicator.__name__)
        #dummy_fields = IndicatorTypeField.objects.filter(
            #indicator_type__classname=DummyIndicator.__name__)
        #self.assertEquals(len(dummy_fields), 2)

        #dummy_indicator.name = 'NewName'
        #dummy_indicator.save()
        #dummy_fields[0].delete()
        #self.assertEqual(dummy_fields[1].field_type.ftype,
                         #DummyIndicator.parameters[dummy_fields[1].field_type.name])

        ## change fieldtype
        #f1 = dummy_fields[1]
        #f1.field_type.ftype = FieldTypes.CLASSIFICATION
        #f1.field_type.save()

        ## add fields
        #IndicatorTypeField.objects.create(indicator_type=dummy_indicator,
                                          #field_type=f1.field_type,
                                          #label='F1')
        #IndicatorTypeField.objects.create(indicator_type=dummy_indicator,
                                          #field_type=f1.field_type,
                                          #label='F2')

        #indicators_values_list = indicator_types.values_list('classname', flat=True)
        #assert set(['Unknown',
                    #DummyIndicator.__name__,
                    #TotalCapacityInArea.__name__,
                    #]).issubset(set(indicators_values_list))

        #assert NumberOfLocations.__name__ not in indicators_values_list

        ## reset the indicators
        #IndicatorType._update_indicators_types()
        #assert set([DummyIndicator.__name__,
                    #NumberOfLocations.__name__,
                    #TotalCapacityInArea.__name__,
                    #])\
               #.issubset(set(indicator_types.values_list('classname', flat=True)))


        #dummy_indicator = IndicatorType.objects.get(classname=DummyIndicator.__name__)
        #dummy_fields = IndicatorTypeField.objects.filter(
            #indicator_type__classname=DummyIndicator.__name__)
        #self.assertEquals(len(dummy_fields), 2)
        #self.assertEquals(dummy_indicator.name, DummyIndicator.label)


class DummyIndicator(ServiceIndicator):
    label = 'TE'
    description = 'Random Indicator'
    parameters = {'Max_Value': FieldTypes.NUMBER, 'TextField': FieldTypes.STRING, }
    userdefined = True

    def compute(self):
        """"""
