from django.test import TestCase
from .factories import (DemandRateSetFactory, DemandRateFactory)


class TestDemand(TestCase):

    def test_demand_rate_set(self):
        demand_rate_set = DemandRateSetFactory()
        demand_rate = DemandRateFactory(demand_rate_set=demand_rate_set)
        print(demand_rate)


