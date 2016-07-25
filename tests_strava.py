import unittest
from storage import redisclient
from strava import Strava
from load_data import loader
import mock

from datetime import datetime, date, timedelta


class tests_Strava(unittest.TestCase):
    test_data = None
    efforts = []

    def setupTestData(self):
        redisclient('localhost', 6379)
        self.test_data = loader().setupTestData(file='test_seed_data.yml')
        self.efforts = self.test_data['loaded_efforts']

    def test_Strava_get_access_token_whenCalled_returnsTestDataToken(self):
        self.setupTestData()
        token = Strava().get_access_token()
        self.assertEqual(token, self.test_data['api_token'])

    def test_Strava_get_efforts_whenCalledWithMockedAPI_returnsEffortsFromTestData(self):
        with mock.patch('webrequest.getjsonfromurl') as mock_geturl:
            self.setupTestData()
            mock_geturl.return_value = self.efforts

            starttime = datetime(year=2016, month=4, day=3, hour=1, minute=2, second=3)
            endtime = datetime(year=2016, month=4, day=10, hour=18, minute=0, second=0)

            efforts = Strava().get_efforts('123456', starttime, endtime)

            args = mock_geturl.call_args[0]
            params = args[1]

            self.assertEqual(params['start_date_local'], '2016-04-03T01:02:03')
            self.assertEqual(params['end_date_local'], '2016-04-10T18:00:00')
            self.assertIn('/123456/', args[0])


if __name__ == "__main__":
    unittest.main()