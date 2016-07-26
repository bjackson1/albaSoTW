import unittest
from storage import redisclient
from load_data import loader
from division import Division
import mock


class tests_Division(unittest.TestCase):
    test_data = None

    def setupTestData(self):
        redisclient('localhost', 6379)
        self.test_data = loader().setupTestData(file='test_seed_data.yml')
        # self.efforts = self.test_data['loaded_efforts']

    def test_Division_get_all_whenCalled_returnsAllDivisionsFromRedis(self):
        self.setupTestData()

        divs = Division.get_all(True)

        return True

    def test_Division_init_whenCalledWithDivisionInRedis_returnsDivisionRecord(self):
        self.setupTestData()

        division = Division('tdiv1')

        return True