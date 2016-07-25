import unittest
from storage import redisclient
from load_data import loader
from athlete import Athlete
import mock


class tests_Athlete(unittest.TestCase):
    test_data = None

    def setupTestData(self):
        redisclient('localhost', 6379)
        self.test_data = loader().setupTestData(file='test_seed_data.yml')
        # self.efforts = self.test_data['loaded_efforts']

    def test_Athlete_init_whenCalledWithAthleteIdNotInRedis_returnsAthleteRecordRetrievedFromStrava(self):
        with mock.patch('webrequest.getjsonfromurl') as mock_geturl:
            self.setupTestData()
            mock_geturl.return_value = self.test_data['members'][1338208]

            redisclient.delete('1338208')
            athlete = Athlete('1338208').get()

            mock_geturl.assert_called()

            self.assertEqual(athlete['firstname'], 'Brett')
            self.assertEqual(athlete['lastname'], 'J ARCC')
            self.assertEqual(athlete['sex'], 'M')

    def test_Athlete_whenCalledWithAthleteIdInRedis_returnsAthleteRecordFromRedis(self):
        with mock.patch('webrequest.getjsonfromurl') as mock_geturl:
            self.setupTestData()
            mock_geturl.return_value = self.test_data['members'][1338208]

            athlete = Athlete('1338208').get()

            mock_geturl.assert_not_called()

            self.assertEqual(athlete['firstname'], 'Brett')
            self.assertEqual(athlete['lastname'], 'J ARCC')
            self.assertEqual(athlete['sex'], 'M')