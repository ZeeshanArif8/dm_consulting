import cardconnect # noqa
from cardconnect.test.helper import (
    CardConnectTest
)

TEST_PROFILE_CREATE = {
    'merchid': '496160873888',
    'account': '9418594164541111',
    'name': 'Test User'
}

TEST_PROFILE_UPDATE = {
    'merchid': '496160873888',
    'profile': '13106769609077182008',
    'account': '9418594164541111',
    'name': 'Test User Updated',
    'profileupdate': 'Y'
}


class ProfileTest(CardConnectTest): # noqa

    def test_profile_create(self): # noqa
        cardconnect.Profile.create(**TEST_PROFILE_CREATE)

        self.requestor_mock.request.assert_called_with(
            'put',
            '/profile',
            TEST_PROFILE_CREATE
        )

    def test_profile_update(self): # noqa
        cardconnect.Profile.update(**TEST_PROFILE_UPDATE)

        self.requestor_mock.request.assert_called_with(
            'put',
            '/profile',
            TEST_PROFILE_UPDATE
        )

    def test_profile_get(self): # noqa
        cardconnect.Profile.get('13106769609077182008', '496160873888')

        self.requestor_mock.request.assert_called_with(
            'get',
            '/profile/13106769609077182008//496160873888',
            {}
        )

    def test_profile_delete(self): # noqa
        cardconnect.Profile.delete('13106769609077182008', '496160873888')

        self.requestor_mock.request.assert_called_with(
            'delete',
            '/profile/13106769609077182008//496160873888',
            {}
        )
