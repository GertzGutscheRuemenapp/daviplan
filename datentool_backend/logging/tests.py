from test_plus import APITestCase
from datentool_backend.api_test import (BasicModelReadTest,
                                        ReadOnlyWithAdminBasedataAccessTest)
from datentool_backend.api_test import TestAPIMixin

from .factories import LogEntryFactory

from ..user.factories import ProfileFactory

from faker import Faker

faker = Faker('de-DE')

# disabled the whole test, does not make much sense for a read only view as it is
# e.g. does not return ids -> no detail view, but tested for that
# should be tested at some point nonetheless

#class TestCapacityUploadLogAPI(ReadOnlyWithAdminBasedataAccessTest,
                               #TestAPIMixin, BasicModelReadTest, APITestCase):
    #""""""
    #url_key = "logs"
    #factory = LogEntryFactory

    #@classmethod
    #def setUpTestData(cls):
        #super().setUpTestData()
        #cls.profile = ProfileFactory()
        ## no idea what to test here, put/patch/post is actually not allowed

