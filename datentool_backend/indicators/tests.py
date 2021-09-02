from django.test import TestCase
from .factories import (ModeVariantFactory, RouterFactory,
                        IndicatorFactory, ReachabilityMatrixFactory)


class TestIndicator(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.mode_variant = ModeVariantFactory()
        cls.router = RouterFactory()
        cls.indicator = IndicatorFactory()
        cls.matrix = ReachabilityMatrixFactory()

    def test_mode_variant(self):
         mode_variant = self.mode_variant

    def test_router(self):
        router = self.router