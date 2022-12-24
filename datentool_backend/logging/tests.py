import logging
import pandas as pd

from test_plus import APITestCase
from datentool_backend.api_test import TestAPIMixin

from datentool_backend.user.factories import ProfileFactory
from .loggers import PersistLogHandler


class TestLogAPI(TestAPIMixin, APITestCase):
    """"""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.profile1 = ProfileFactory(can_edit_basedata=False, admin_access=False)
        cls.profile2 = ProfileFactory(can_edit_basedata=False, admin_access=False)

    def test_logging(self):
        """test if a log entrace shows up in the logging api"""
        url = 'logs-list'
        res = self.get(url)
        self.assert_http_401_unauthorized(res)
        self.client.force_login(self.profile1.user)
        res = self.get(url)
        self.assert_http_403_forbidden(res)
        self.profile1.can_edit_basedata = True
        self.profile1.save()
        res = self.get(url)
        self.assert_http_200_ok(res)
        self.assertEqual(res.data, [])

        p1 = self.profile1.pk
        p2 = self.profile2.pk

        expected_data = []

        hdlr1 = PersistLogHandler(user=self.profile1)

        room1 = 'population'
        logger = logging.getLogger(room1)
        logger.setLevel(logging.WARN)
        hdlr1 = PersistLogHandler.register(user=self.profile1)

        logger.debug('Population Debug Message')
        logger.info('Population Info Message')
        logger.warn('Population Warn Message')
        expected_data.append([p1, 'WARNING', room1, None])
        logger.error('Population Error Message')
        expected_data.append([p1, 'ERROR', room1, None])

        # until here, only warn and messages should appear
        logger.setLevel(logging.INFO)
        # now also the info message
        logger.debug('Population Debug Message')
        logger.info('Population Info Message')
        expected_data.append([p1, 'INFO', room1, None])
        logger.warn('Population warn Message with status', extra=dict(status='take care'))
        expected_data.append([p1, 'WARNING', room1, 'take care'])

        # create handler for profile 2 with error level
        hdlr2 = PersistLogHandler.register(user=self.profile2)
        hdlr2.setLevel(logging.ERROR)

        logger.warn('Warning to Profile 1')
        expected_data.append([p1, 'WARNING', room1, None])
        logger.error('Error to Profile 1+2')
        expected_data.append([p1, 'ERROR', room1, None])
        expected_data.append([p2, 'ERROR', room1, None])

        # remove first handler
        logger.removeHandler(hdlr1)
        logger.error('Error to Profile 2')
        expected_data.append([p2, 'ERROR', room1, None])

        room2 = 'routing'
        logger2 = logging.getLogger(room2)
        logger2.addHandler(hdlr1)
        logger2.addHandler(hdlr2)
        logger2.setLevel(logging.DEBUG)
        logger2.debug('Routing debug message')
        expected_data.append([p1, 'DEBUG', room2, None])
        logger2.error('Routing error message')
        expected_data.append([p1, 'ERROR', room2, None])
        expected_data.append([p2, 'ERROR', room2, None])

        room_not_registred = 'notRegistred'
        logger3 = logging.getLogger(room_not_registred)
        logger3.warn('this message should not be saved as a LogEntry')

        room_manually_registred = 'manuallyRegistred'
        logger4 = logging.getLogger(room_manually_registred)
        logger4.addHandler(hdlr1)
        logger4.error('this message should shown at profile 1')
        expected_data.append([p1, 'ERROR', room_manually_registred, None])

        res = self.get(url)
        self.assert_http_200_ok(res)
        self.assertContains(res, room1)
        self.assertContains(res, room2)
        self.assertNotContains(res, room_not_registred)
        self.assertContains(res, room_manually_registred)

        df = pd.DataFrame(res.data)
        self.assertEqual(df['message'].iloc[0], 'Population Warn Message')
        actual = df[['user', 'level', 'room', 'status']]
        expected = pd.DataFrame(data=expected_data, columns=actual.columns)
        pd.testing.assert_frame_equal(actual, expected)
