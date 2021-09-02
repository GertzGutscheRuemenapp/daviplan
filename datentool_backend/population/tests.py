from django.test import TestCase
from .factories import (RasterCellFactory)


class TestPopulation(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.cell = RasterCellFactory()

    def test_cell(self):
         cell = self.cell
