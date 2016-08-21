import unittest
from storage import redisclient
from load_data import loader
from division import Division
from segment_of_the_week import SegmentOfTheWeek
import mock
from mock import patch


class tests_Division(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        redisclient('localhost', 6379, db=1)
        super(tests_Division, self).__init__(*args, **kwargs)


    def setupTestData(self):
        self.test_data = loader().setupTestData(file='../test_seed_data.yml')


    def test_Division_get_all_whenCalledWithGetAthletesFlag_returnsAllDivisionsAndAthletesFromRedis(self):
        self.setupTestData()
        divs = Division.get_all()

        self.assertTrue('tdiv1' in divs, 'Division tdiv1 not found in returned dict')
        self.assertTrue('tbotr' in divs, 'Division tdiv1 not found in returned dict')
        self.assertTrue(10000005 in divs['tdiv1'].members)
        self.assertEqual(divs['tdiv1'].members[10000005].firstname, 'User')


    def test_Division_add_athlete_whenCalledWithNewAthlete_addsToCorrectDivision(self):
        self.setupTestData()
        division = Division('tbotr')
        division.add_athlete(123456)

        self.assertTrue('123456' in redisclient.smembers('tbotr_members'))

        division.remove_athlete('123456')


    # def test__Division__init__whenCalledWithMockedAthletes_buildsPopulatedMembersField(self):
    #     with mock.patch('strava.Strava.get_athlete') as mock_get_athlete:
    #
    #         mock_get_athlete.return_value = [
    #             {"id": "1234565", "activity": {"id": "2345676"}, "athlete": {"id": 10000001}, "elapsed_time": 1100, "distance": 10000},
    #             {"id": "1234566", "activity": {"id": "2345677"}, "athlete": {"id": 10000003}, "elapsed_time": 1050, "distance": 10000},
    #             {"id": "1234567", "activity": {"id": "2345678"}, "athlete": {"id": 10000002}, "elapsed_time": 1200, "distance": 10000},

