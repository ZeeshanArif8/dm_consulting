import os # noqa
import unittest2

from mock import patch, Mock

import cardconnect


class CardConnectTest(unittest2.TestCase): # noqa
    REQUESTOR_CLS_NAME = 'cardconnect.api_requestor.ApiRequestor'

    def setUp(self): # noqa
        super(CardConnectTest, self).setUp()

        cardconnect.username = 'testing'
        cardconnect.password = 'testing123'
        cardconnect.base_url = 'fts.cardconnect.com:6443'
        cardconnect.debug = True

        self.requestor_patcher = patch(self.REQUESTOR_CLS_NAME)
        requestor_class_mock = self.requestor_patcher.start()

        self.requestor_mock = requestor_class_mock.return_value
        self.requestor_mock.request = Mock(return_value=({}, 'reskey'))

    def tearDown(self): # noqa
        super(CardConnectTest, self).tearDown()

        self.requestor_patcher.stop()
