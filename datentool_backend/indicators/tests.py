from django.test import TestCase
from .factories import (ModeVariantFactory, RouterFactory,
                        IndicatorFactory, ReachabilityMatrixFactory)


class TestIndicator(TestCase):

    def test_mode_variant(self):
        mode_variant = ModeVariantFactory()

    def test_router(self):
        router = RouterFactory()

    def test_indicator(self):
        indicator = IndicatorFactory()

    def test_matrix(self):
        matrix = ReachabilityMatrixFactory()