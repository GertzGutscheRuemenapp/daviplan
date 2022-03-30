from datentool_backend.indicators.compute.base import ComputeIndicator, ResultSerializer


class ReachabilityPlace(ComputeIndicator):
    '''Wegezeit zwischen ausgewählter Einrichtung und allen Wohnstandorten
    (= Rasterzellen)'''
    title = 'Erreichbarkeit Einrichtung'
    description = ('Wegezeit zwischen ausgewählter Einrichtung und allen '
                   'Wohnstandorten (= Rasterzellen) ')
    result_serializer = ResultSerializer.RASTER

    def compute(self):
        return []


class ReachabilityCell(ComputeIndicator):
    '''Wegezeit zwischen ausgewähltem Wohnstandort (= Rasterzelle) und allen
    Einrichtungen'''
    title = 'Erreichbarkeit Wohnstandort'
    description = ('Wegezeit zwischen ausgewähltem Wohnstandort (= Rasterzelle) '
                   'und allen Einrichtungen')
    result_serializer = ResultSerializer.PLACE

    def compute(self):
        return []