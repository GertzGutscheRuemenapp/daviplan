import logging
from typing import List
import pandas as pd

from test_plus import APITestCase
from datentool_backend.api_test import LoginTestCase

from datentool_backend.user.factories import ProfileFactory
from .loggers import PersistLogHandler


class TestLogAPI(LoginTestCase, APITestCase):
    """"""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.profile2 = ProfileFactory(can_edit_basedata=True, admin_access=False)
        cls.room_not_registred = 'notRegistred'
        cls.room_manually_registred = 'manuallyRegistred'
        cls.logger_names = PersistLogHandler.loggers + [cls.room_not_registred,
                                                        cls.room_manually_registred]
        cls.remove_existing_handlers(cls.logger_names)

    @classmethod
    def tearDownClass(cls):
        user = cls.profile2.user
        user.delete()
        cls.profile2.delete()
        del cls.profile2
        super().tearDownClass()

    @staticmethod
    def remove_existing_handlers(logger_names: List[str]):
        '''remove existing handlers for the PersisLogHandler-Loggers'''
        for logger_name in logger_names:
            logger = logging.getLogger(logger_name)
            for hdlr in list(logger.handlers):
                logger.removeHandler(hdlr)

    def test_logging(self):
        """test if a log entrance shows up in the logging api"""
        url = 'logs-list'

        # standard profile has no admin_access or can_edit_basedata
        res = self.get(url)
        self.assert_http_403_forbidden(res)

        # profile2 can_edit_basedata and may get the log entries
        self.client.force_login(self.profile2.user)
        res = self.get(url)
        self.assert_http_200_ok(res)
        self.assertEqual(res.data, [])

        p1 = self.profile.pk
        p2 = self.profile2.pk

        expected_data = []

        #  create handler for p1 and regsiter with the logger rooms population, routing ...
        room1 = 'population'
        pop_logger = logging.getLogger(room1)
        pop_logger.setLevel(logging.WARN)

        room2 = 'routing'
        routing_logger = logging.getLogger(room2)
        routing_logger.setLevel(logging.DEBUG)

        hdlr1 = PersistLogHandler.register(user=self.profile)

        # log some messages to the population room
        pop_logger.debug('Population Debug Message')
        pop_logger.info('Population Info Message')
        # until here, only warn and messages should appear because log level = WARNING

        pop_logger.warn('Population Warn Message')
        expected_data.append([p1, 'WARNING', room1, None])
        pop_logger.error('Population Error Message')
        expected_data.append([p1, 'ERROR', room1, None])

        pop_logger.setLevel(logging.INFO)
        # now also the info message should appera
        pop_logger.debug('Population Debug Message')
        pop_logger.info('Population Info Message')
        expected_data.append([p1, 'INFO', room1, None])

        # log an extra status message
        pop_logger.warn('Population warn Message with status', extra=dict(status='take care'))
        expected_data.append([p1, 'WARNING', room1, 'take care'])

        # create handler for profile 2 with error level and register with logger rooms
        hdlr2 = PersistLogHandler.register(user=self.profile2)
        hdlr2.setLevel(logging.ERROR)

        pop_logger.warn('Warning to Profile 1')
        expected_data.append([p1, 'WARNING', room1, None])
        pop_logger.error('Error to Profile 1+2')
        expected_data.append([p1, 'ERROR', room1, None])
        expected_data.append([p2, 'ERROR', room1, None])

        # remove first handler
        pop_logger.removeHandler(hdlr1)
        pop_logger.error('Error to Profile 2')
        expected_data.append([p2, 'ERROR', room1, None])

        # the handlers should be registred with the routing-room

        routing_logger.debug('Routing debug message')
        expected_data.append([p1, 'DEBUG', room2, None])
        routing_logger.error('Routing error message')
        expected_data.append([p1, 'ERROR', room2, None])
        expected_data.append([p2, 'ERROR', room2, None])

        # for this logger, no LogEntry-Handler is registred
        logger3 = logging.getLogger(self.room_not_registred)
        logger3.warn('this message should not be saved as a LogEntry')

        # for this logger, manually register hdlr1
        logger4 = logging.getLogger(self.room_manually_registred)
        logger4.addHandler(hdlr1)
        logger4.error('this message should shown at profile 1')
        expected_data.append([p1, 'ERROR', self.room_manually_registred, None])

        res = self.get(url)
        self.assert_http_200_ok(res)
        self.assertContains(res, room1)
        self.assertContains(res, room2)
        self.assertNotContains(res, self.room_not_registred)
        self.assertContains(res, self.room_manually_registred)

        df = pd.DataFrame(res.data)
        self.assertEqual(df['message'].iloc[0], 'Population Warn Message')
        actual = df[['user', 'level', 'room', 'status']]
        expected = pd.DataFrame(data=expected_data, columns=actual.columns)
        pop_logger.info(str(actual))
        pd.testing.assert_frame_equal(actual, expected)
