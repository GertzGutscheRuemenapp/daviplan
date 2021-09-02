from django.test import TestCase
from .factories import (InfrastructureFactory, ServiceFactory)


class TestInfrastructure(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.infrastructure = InfrastructureFactory()
        cls.service = ServiceFactory()

    def test_service(self):
         service = self.service
