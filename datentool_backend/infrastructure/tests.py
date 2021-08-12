from hypothesis.extra.django import TestCase, from_model
from hypothesis import given
from hypothesis.strategies import integers, lists, just
from ..models import SymbolForm, MapSymbols, LayerGroup, InternalWFSLayer



class InfrastructureTestCase(TestCase):

    @given(from_model(MapSymbols, symbol=from_model(SymbolForm)))
    def test_map_symbols(self, map_symbol):
        self.assertIsInstance(map_symbol, MapSymbols)
        self.assertIsInstance(map_symbol.symbol, SymbolForm)
        self.assertIsNotNone(map_symbol.pk)
