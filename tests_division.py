import unittest
from storage import redisclient
from load_data import loader
from division import Division

class tests_Division(unittest.TestCase):
    test_data = None

    def __init__(self, *args, **kwargs):
        super(tests_Division, self).__init__(*args, **kwargs)
        self.setupTestData()

    def setupTestData(self):
        redisclient('localhost', 6379)
        self.test_data = loader().setupTestData(file='test_seed_data.yml')
        # self.efforts = self.test_data['loaded_efforts']

    def test_Division_get_all_whenCalledWithGetAthletesFlag_returnsAllDivisionsAndAthletesFromRedis(self):
        divs = Division.get_all(True)

        self.assertTrue('tdiv1' in divs, 'Division tdiv1 not found in returned dict')
        self.assertTrue('tbotr' in divs, 'Division tdiv1 not found in returned dict')

        self.assertTrue('10000004' in divs['tdiv1']['members'])

        self.assertTrue('firstname' in divs['tdiv1']['members']['10000004'])
        self.assertEqual(divs['tdiv1']['members']['10000004']['firstname'], 'User')

    def test_Division_get_all_whenCalledWithoutGetAthletesFlag_returnsAllDivisionsAndAthletesListFromRedis(self):
        divs = Division.get_all(False)

        self.assertTrue('tdiv1' in divs, 'Division tdiv1 not found in returned dict')
        self.assertTrue('tbotr' in divs, 'Division tdiv1 not found in returned dict')

        self.assertTrue('10000004' in divs['tdiv1']['members'])

        self.assertFalse('firstname' in divs['tdiv1']['members']['10000004'])

    def test_Division_add_athlete_whenCalledWithNewAthlete_addsToCorrectDivision(self):
        division = Division('tbotr')

        division.add_athlete('123456')

        self.assertTrue('123456' in redisclient.smembers('tbotr_members'))

        division.remove_athlete_from_division('tbotr', '123456')

