from .base import ComputeIndicator, ResultSerializer


#@register_indicator_class()
class IntersectAreaWithRaster(ComputeIndicator):
    result_serializer = ResultSerializer.RASTER

    def compute(self):
        """"""


#@register_indicator_class()
class DisaggregatePopulation(ComputeIndicator):
    result_serializer = ResultSerializer.RASTER

    def compute(self):
        """"""
