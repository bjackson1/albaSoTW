import unittest
import svr
import mock
from load_data import loader


class tests_svr(unittest.TestCase):
    efforts = []
    test_data = None

    def setupTestData(self):
        self.test_data = loader().setupTestData(file='test_seed_data.yml')
        self.efforts = self.test_data['loaded_efforts']

    def test_svr_compile_efforts_whenCalled_returnsDictOfDictsWithValidResults(self):
        with mock.patch('webrequest.getjsonfromurl') as mock_geturl:
            self.setupTestData()
            mock_geturl.return_value = self.efforts
            ret = svr.compile_efforts()

            if ret['tbotr']:
                botr = ret['tbotr']

                self.assertEqual(len(botr), 3)

                self.assertTrue(botr[10000001], "Athlete 10000001 expected in data set, but not found")
                self.assertTrue(botr[10000002], "Athlete 10000002 expected in data set, but not found")
                self.assertTrue(botr[10000003], "Athlete 10000003 expected in data set, but not found")

                self.assertEqual(botr[10000001]['elapsed_time'], 101, "Athlete 10000001 expected elapsed time is incorrect")
                self.assertEqual(botr[10000002]['elapsed_time'], 101, "Athlete 10000002 expected elapsed time is incorrect")
                self.assertEqual(botr[10000003]['elapsed_time'], 150, "Athlete 10000003 expected elapsed time is incorrect")

                self.assertEqual(botr[10000001]['rank'], 1, "Athlete 10000001 expected rank is incorrect")
                self.assertEqual(botr[10000002]['rank'], 1, "Athlete 10000002 expected rank is incorrect")
                self.assertEqual(botr[10000003]['rank'], 3, "Athlete 10000003 expected rank is incorrect")

                self.assertEqual(botr[10000001]['points'], 10, "Athlete 10000001 expected points is incorrect")
                self.assertEqual(botr[10000002]['points'], 10, "Athlete 10000002 expected points is incorrect")
                self.assertEqual(botr[10000003]['points'], 8, "Athlete 10000003 expected points is incorrect")

                # self.assertEqual(botr[10000001]['start_time_formatted'], "01:30, Thursday 21/07/2016",
                #                  "Formatted start date is incorrect")
                # self.assertEqual(botr[10000002]['start_time_formatted'], "03:30, Thursday 21/07/2016",
                #                  "Formatted start date is incorrect")
                # self.assertEqual(botr[10000003]['start_time_formatted'], "04:30, Thursday 21/07/2016",
                #                  "Formatted start date is incorrect")

            else:
                self.fail("tbotr league missing from results")

    def test_svr_compile_efforts_whenCalled_returnsCompiledDictOfAllLeagues(self):
        svr.init()
        svr.loadintdata()
        ret = svr.compile_efforts()


if __name__ == "__main__":
    unittest.main()