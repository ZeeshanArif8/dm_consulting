import cardconnect # noqa
from cardconnect.test.helper import (
    CardConnectTest
)


class FundingTest(CardConnectTest): # noqa

    def test_funding_get(self): # noqa
        cardconnect.Funding.get('496160873888', '0419')

        self.requestor_mock.request.assert_called_with(
            'get',
            '/funding?merchid=496160873888&date=0419',
            {}
        )
