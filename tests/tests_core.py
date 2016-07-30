import unittest
import mock
from load_data import loader
from core import AlbaSotwCore
from datetime import date
from storage import redisclient

class tests_AlbaSotwCore(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        redisclient('localhost', 6379, db=1)
        super(tests_AlbaSotwCore, self).__init__(*args, **kwargs)
        self.test_data = loader().setupTestData(file='../test_seed_data.yml')
        self.efforts = self.test_data['loaded_efforts']

    def test_core_compile_efforts_whenCalled_returnsDictOfDictsWithValidResults(self):
        with mock.patch('webrequest.getjsonfromurl') as mock_geturl:
            # mock_geturl.side_effect = [self.efforts, self.test_data['loaded_neutral_zones']]
            mock_geturl.return_value = self.efforts

            core = AlbaSotwCore()

            ret = core.compile_efforts()

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

    def test_core_get_sotw_key_name_whenCalledWithNoParameters_returnsKeyNameForThisWeek(self):
        core = AlbaSotwCore()

        today = date.today()
        year = today.year
        week_number = today.isocalendar()[1]

        expected_key_name = 'sotw_%s_%s' % (year, week_number)
        returned_key_name = core.get_sotw_key_name()

        self.assertEqual(expected_key_name, returned_key_name)

    def test_core_get_sotw_key_name_whenCalledWithParameters_returnsKeyNameWithParameters(self):
        core = AlbaSotwCore()

        expected_key_name = 'sotw_2015_31'
        returned_key_name = core.get_sotw_key_name(year=2015, week_number=31)

        self.assertEqual(expected_key_name, returned_key_name)

    def test_core_add_sotw_whenCalledWithNoNeutralZones_persistsData(self):
        core = AlbaSotwCore()

        core.add_sotw(123456)
        key_name = core.get_sotw_key_name()

        segment_id = redisclient.get('%s_segment' % key_name)
        neutral_zones = redisclient.smembers('%s_neutral_zones' % key_name)

        self.assertEqual(segment_id, '123456')
        self.assertEqual(len(neutral_zones), 0)

        return True

    def test_core_add_sotw_whenCalledWithNeutralZones_persistsData(self):
        core = AlbaSotwCore()
        key_name = core.get_sotw_key_name()

        redisclient.delete('%s_segment' % key_name)
        redisclient.delete('%s_neutral_zones' % key_name)

        core.add_sotw(123456, [234567, 345678, 456789])

        segment_id = redisclient.get('%s_segment' % key_name)
        neutral_zones = redisclient.smembers('%s_neutral_zones' % key_name)

        self.assertEqual(segment_id, '123456')
        self.assertEqual(len(neutral_zones), 3)
        self.assertTrue('234567' in neutral_zones)
        self.assertTrue('345678' in neutral_zones)
        self.assertTrue('456789' in neutral_zones)

if __name__ == "__main__":
    unittest.main()