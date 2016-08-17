import unittest
import mock
from load_data import loader
from core import AlbaSotwCore
from datetime import date
from storage import redisclient
from unittest.mock import patch

class tests_AlbaSotwCore(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        redisclient('localhost', 6379, db=1)
        super(tests_AlbaSotwCore, self).__init__(*args, **kwargs)
        self.test_data = loader().setupTestData(file='../test_seed_data.yml')
        self.efforts = self.test_data['loaded_efforts']

    def test_core_compile_efforts_whenCalled_returnsCorrectDivisionNames(self):
        with mock.patch('webrequest.getjsonfromurl') as mock_geturl:
            mock_geturl.return_value = self.efforts

            core = AlbaSotwCore()

            ret = core.compile_efforts()

            self.assertEqual(ret['tdiv1']['name'], 'Division 1')

    def test_core_compile_efforts_whenCalled_returnsDictOfDictsWithValidResults(self):
        key_name = 'sotw_2016_30'
        redisclient.delete('%s_segment' % key_name)
        redisclient.delete('%s_neutral_zones' % key_name)

        redisclient.set('%s_segment' % key_name, '6216534')
        redisclient.sadd('%s_neutral_zones' % key_name, '12721002')
        redisclient.sadd('%s_neutral_zones' % key_name, '12745854')

        core = AlbaSotwCore()

        ret = core.compile_efforts('2016', '30')

        if ret['tdiv1']:
            div1 = ret['tdiv1']['results']

            self.assertEqual(len(div1), 3)

            self.assertTrue(div1[1319585], "Athlete 1319585 expected in data set, but not found")
            self.assertTrue(div1[776351], "Athlete 776351 expected in data set, but not found")
            self.assertTrue(div1[2198262], "Athlete 2198262 expected in data set, but not found")

            self.assertEqual(div1[1319585]['elapsed_time'], 1394, "Athlete 1319585 expected elapsed time is incorrect")
            self.assertEqual(div1[776351]['elapsed_time'], 1156, "Athlete 776351 expected elapsed time is incorrect")
            self.assertEqual(div1[2198262]['elapsed_time'], 1295, "Athlete 2198262 expected elapsed time is incorrect")

            self.assertEqual(div1[1319585]['corrected_time'], 1343, "Athlete 1319585 expected corrected time is incorrect")
            self.assertEqual(div1[776351]['corrected_time'], 1109, "Athlete 776351 expected corrected time is incorrect")
            self.assertEqual(div1[2198262]['corrected_time'], 1223, "Athlete 2198262 expected corrected time is incorrect")

            self.assertEqual(div1[1319585]['rank'], 3, "Athlete 1319585 expected rank is incorrect")
            self.assertEqual(div1[776351]['rank'], 1, "Athlete 776351 expected rank is incorrect")
            self.assertEqual(div1[2198262]['rank'], 2, "Athlete 2198262 expected rank is incorrect")

            self.assertEqual(div1[1319585]['points'], 8, "Athlete 1319585 expected points is incorrect")
            self.assertEqual(div1[776351]['points'], 10, "Athlete 776351 expected points is incorrect")
            self.assertEqual(div1[2198262]['points'], 9, "Athlete 2198262 expected points is incorrect")

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

    # def test_core_add_sotw_whenCalledWithNoNeutralZones_persistsData(self):
    #     core = AlbaSotwCore()
    #
    #     core.add_sotw(123456)
    #     key_name = core.get_sotw_key_name()
    #
    #     segment_id = redisclient.get('%s_segment' % key_name)
    #     neutral_zones = redisclient.smembers('%s_neutral_zones' % key_name)
    #
    #     self.assertEqual(segment_id, '123456')
    #     self.assertEqual(len(neutral_zones), 0)
    #
    #     return True

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

# @patch('webrequest.getjsonfromurl')
# def getjsonfromurl(uri, parameters=None, token=None):
#     return None

if __name__ == "__main__":
    unittest.main()