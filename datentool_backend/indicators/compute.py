from abc import ABCMeta


class ComputeIndicator(metaclass=ABCMeta):

    def __init__(self,
                 service:int,
                 area_level: int,
                 scenario: int=None,
                 year: int=None,
                 ):
        self.service = service
        self.area_level = area_level
        self.scenario = scenario
        self.year = year

    def compute(self):
        """compute the indicator"""
        return NotImplemented


class NumberOfLocations(ComputeIndicator):

    def compute(self):
        """"""