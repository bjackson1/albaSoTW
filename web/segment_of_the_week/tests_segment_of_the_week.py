import unittest
from datetime import date, datetime
from storage import redisclient
from unittest.mock import patch
from segment_of_the_week import SegmentOfTheWeek

class tests_SegmentOfTheWeek(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        redisclient('localhost', 6379, db=1)
        super(tests_SegmentOfTheWeek, self).__init__(*args, **kwargs)
        self.setup_test_data()
        self.test_instance = SegmentOfTheWeek()


    def test__segment_of_the_week__get_period__whenCalledWithNoValues__returnsPeriodForCurrentWeek(self):
        expected_year, expected_week_number = self.get_current_year_and_week_number()

        year, week_number = self.test_instance.get_period()

        self.assertEqual(year, expected_year)
        self.assertEqual(week_number, expected_week_number)


    def test__segment_of_the_week__get_period__whenCalledWithYearAndWeekNumber__returnsPeriodForExpectedWeek(self):
        expected_year, expected_week_number = 2016, 2

        year, week_number = self.test_instance.get_period(expected_year, expected_week_number)

        self.assertEqual(year, expected_year)
        self.assertEqual(week_number, expected_week_number)


    def test__segment_of_the_week__get_key_name__whenCalled__returnsFormattedKeyName(self):
        expected_year, expected_week_number = self.get_current_year_and_week_number()
        expected_key_name = 'sotw_%s_%s' % (expected_year, expected_week_number)

        sotw = SegmentOfTheWeek()

        self.assertEqual(sotw.get_key_name(), expected_key_name)


    def test__segment_of_the_week__get_key_name__whenCalledWithSingleDigitWeekNumber__returnsFormattedKeyNameWithPaddedWeekNumber(self):
        expected_year, expected_week_number = 2016, 2
        expected_key_name = 'sotw_2016_02'

        sotw = SegmentOfTheWeek(expected_year, expected_week_number)

        self.assertEqual(sotw.get_key_name(), expected_key_name)


    def test__segment_of_the_week__get_start_and_end_datetimes__whenCalledWithYearAndWeekNumber__returnsExpectedStartAndEndDataTimesForMondayToSunday(self):
        expected_start_datetime = datetime(year=2016, month=6, day=13, hour=0, minute=0)
        expected_end_datetime = datetime(year=2016, month=6, day=19, hour=20, minute=0)

        sotw = SegmentOfTheWeek(2016, 24)
        start_datetime, end_datetime = sotw.get_start_end_datetimes()

        self.assertEqual(start_datetime, expected_start_datetime)
        self.assertEqual(end_datetime, expected_end_datetime)


    def test__segment_of_the_week__get_segment_ids__whenCalledWithYearAndWeekNumberWithPopulatedData__returnsSetsExpectedSegmentNumber(self):
        expected_segment_id = 6784576
        expected_neutral_zone_ids = {7097863, 768320468}

        sotw = SegmentOfTheWeek(2016, 1)

        self.assertEqual(sotw.main_segment_id, expected_segment_id)
        self.assertEqual(sotw.neutral_zone_ids, expected_neutral_zone_ids)


    def test__segment_of_the_week__get_segment_ids__whenCalledWithYearAndWeekNumberWithUnpopulatedData__returnsNoneAndEmptySet(self):
        sotw = SegmentOfTheWeek(2016, 3)

        self.assertEqual(sotw.main_segment_id, None)
        self.assertEqual(sotw.neutral_zone_ids, set())


    def test__segment_of_the_week__init__whenCalledWithDefinedAndPopulatedYearAndWeekNumber__setsUpObjectWithDefinedValues(self):
        expected_segment_id = 6784576
        expected_neutral_zone_ids = {7097863, 768320468}
        expected_start_datetime = datetime(year=2016, month=1, day=4, hour=0, minute=0)
        expected_end_datetime = datetime(year=2016, month=1, day=10, hour=20, minute=0)
        expected_key_name = 'sotw_2016_01'

        sotw = SegmentOfTheWeek(2016, 1)

        self.assertEqual(sotw.main_segment_id, expected_segment_id)
        self.assertEqual(sotw.neutral_zone_ids, expected_neutral_zone_ids)
        self.assertEqual(sotw.start_datetime, expected_start_datetime)
        self.assertEqual(sotw.end_datetime, expected_end_datetime)
        self.assertEqual(sotw.key_name, expected_key_name)


    def test__segment_of_the_week__init__whenCalledWithNewNewSegmentsAndDefinedYearAndWeekNumber__setsUpObjectWithDefinedValues(self):
        expected_segment_id = 9201348
        expected_neutral_zone_ids = {4324242, 92347892}
        expected_year, expected_week_number = 2016, 4

        sotw = SegmentOfTheWeek(year=2016, week_number=4, main_segment_id=expected_segment_id, neutral_zone_ids=expected_neutral_zone_ids)

        self.assertEqual(sotw.main_segment_id, expected_segment_id)
        self.assertEqual(sotw.neutral_zone_ids, expected_neutral_zone_ids)
        self.assertEqual(sotw.year, expected_year)
        self.assertEqual(sotw.week_number, expected_week_number)


    def test__segment_of_the_week__init__whenCalledWithNewNewSegmentsAndNoYearOrWeekNumber__setsUpObjectWithDefinedValuesForThisWeek(self):
        expected_segment_id = 9201348
        expected_neutral_zone_ids = {4324242, 92347892}
        expected_year, expected_week_number = self.get_current_year_and_week_number()

        sotw = SegmentOfTheWeek(main_segment_id=expected_segment_id, neutral_zone_ids=expected_neutral_zone_ids)

        self.assertEqual(sotw.main_segment_id, expected_segment_id)
        self.assertEqual(sotw.neutral_zone_ids, expected_neutral_zone_ids)
        self.assertEqual(sotw.year, expected_year)
        self.assertEqual(sotw.week_number, expected_week_number)


    def test__segment_of_the_week__save__whenInitAndSaveWithNewNewSegmentsAndDefinedYearOrWeekNumber__createsDefinedDataInRedis(self):
        expected_segment_id = 9201348
        expected_neutral_zone_ids = {4324242, 92347892}
        main_segment_key_name = 'sotw_2016_04_segment'
        neutral_zones_key_name = 'sotw_2016_04_neutral_zones'

        redisclient.delete(main_segment_key_name)
        redisclient.delete(neutral_zones_key_name)

        sotw = SegmentOfTheWeek(year=2016, week_number=4, main_segment_id=expected_segment_id, neutral_zone_ids=expected_neutral_zone_ids)
        sotw.save()

        self.assertEqual(int(redisclient.get(main_segment_key_name)), expected_segment_id)

        stored_neutral_zone_ids = redisclient.smembers(neutral_zones_key_name)
        for neutral_zone_id in expected_neutral_zone_ids:
            self.assertIn(str(neutral_zone_id), stored_neutral_zone_ids)


    def test__segment_of_the_week__save__whenInitAndSaveWithNewNewSegmentsAndNoNeutralZones__createsDefinedDataInRedis(self):
        expected_segment_id = 8940323
        expected_neutral_zone_ids = set()
        main_segment_key_name = 'sotw_2016_04_segment'
        neutral_zones_key_name = 'sotw_2016_04_neutral_zones'

        redisclient.delete(main_segment_key_name)
        redisclient.delete(neutral_zones_key_name)

        sotw = SegmentOfTheWeek(year=2016, week_number=4, main_segment_id=expected_segment_id, neutral_zone_ids=expected_neutral_zone_ids)
        sotw.save()

        self.assertEqual(int(redisclient.get(main_segment_key_name)), expected_segment_id)
        self.assertEqual(redisclient.smembers(neutral_zones_key_name), expected_neutral_zone_ids)


    def test_segment_of_the_week__init__whenCalledWithValidValues__throwsException(self):
        try:
            sotw = SegmentOfTheWeek(year='2000')
            self.assertTrue(sotw.year, 2000)
        except:
            self.fail("Exception raised when valid year value passed as string")

        try:
            sotw = SegmentOfTheWeek(year=2000)
            self.assertTrue(sotw.year, 2000)
        except:
            self.fail("Exception raised when valid low year value passed")

        try:
            sotw = SegmentOfTheWeek(year=2999)
            self.assertTrue(sotw.year, 2999)
        except:
            self.fail("Exception raised when valid high year value passed")

        try:
            sotw = SegmentOfTheWeek(week_number='1')
            self.assertTrue(sotw.week_number, 1)
        except:
            self.fail("Exception raised when valid week_number value passed as string")

        try:
            sotw = SegmentOfTheWeek(week_number=1)
            self.assertTrue(sotw.week_number, 1)
        except:
            self.fail("Exception raised when valid low week_number value passed")

        try:
            sotw = SegmentOfTheWeek(week_number=52)
            self.assertTrue(sotw.week_number, 52)
        except:
            self.fail("Exception raised when valid high week_number value passed")

        try:
            sotw = SegmentOfTheWeek(main_segment_id='123456789')
            self.assertTrue(sotw.main_segment_id, 123456789)
        except:
            self.fail("Exception raised when valid main_segment_id passed as string")

        try:
            sotw = SegmentOfTheWeek(main_segment_id=123456789, neutral_zone_ids=set(['23456789', '34567890']))
            self.assertTrue(sotw.neutral_zone_ids, [23456789, 34567890])
        except:
            self.fail("Exception raised when valid neutral_zone_ids passed as strings")

        sotw = SegmentOfTheWeek(year='2004', week_number='23', main_segment_id='123456789', neutral_zone_ids=set(['23456789', '34567890']))
        self.assertTrue(sotw.year, 2004)
        self.assertTrue(sotw.week_number, 23)
        self.assertTrue(sotw.main_segment_id, 123456789)
        self.assertTrue(sotw.neutral_zone_ids, set([23456789, 34567890]))


    def test_segment_of_the_week__init__whenCalledWithInvalidValues__throwsException(self):
        try:
            SegmentOfTheWeek(year='not a number')
            self.fail("Expected exception due to passed year as a string that does not contain a number")
        except Exception as e:
            self.assertRaises(Exception, "Incorrect exception type due to passed year as a string that does not contain a number")

        try:
            SegmentOfTheWeek(year=1999)
            self.fail("Expected exception due to passed year that is a low out of range number")
        except Exception as e:
            self.assertRaises(Exception, "Incorrect exception type due to passed year that is a low out of range number")

        try:
            SegmentOfTheWeek(year=2999)
            self.fail("Expected exception due to passed year that is a high out of range number")
        except Exception as e:
            self.assertRaises(Exception, "Incorrect exception type due to passed year that is a high out of range number")

        try:
            SegmentOfTheWeek(week_number=53)
            self.fail("Expected exception due to passed week_number that is a high out of range number")
        except Exception as e:
            self.assertRaises(Exception, "Incorrect exception type due to passed week_number that is a high out of range number")

        try:
            SegmentOfTheWeek(week_number=0)
            self.fail("Expected exception due to passed week_number that is a low out of range number")
        except Exception as e:
            self.assertRaises(Exception, "Incorrect exception type due to passed week_number that is a low out of range number")

        try:
            SegmentOfTheWeek(week_number='not a number')
            self.fail("Expected exception due to passed week_number as a string that does not contain a number")
        except Exception as e:
            self.assertRaises(Exception, "Incorrect exception type due to passed week_number as a string that does not contain a number")

        try:
            SegmentOfTheWeek(main_segment_id='not a number')
            self.fail("Expected exception due to passed main_segment_id as a string that does not contain a number")
        except Exception as e:
            self.assertRaises(Exception, "Incorrect exception type due to passed main_segment_id as a string that does not contain a number")

        try:
            SegmentOfTheWeek(neutral_zone_ids='not a set')
            self.fail("Expected exception due to passed neutral_zone_ids that does not contain a set")
        except Exception as e:
            self.assertRaises(Exception, "Incorrect exception type due to passed neutral_zone_ids that does not contain a set")

        try:
            SegmentOfTheWeek(neutral_zone_ids=[123456789, 'not a number'])
            self.fail("Expected exception due to passed neutral_zone_ids that contains a string that is not a number as part of a set")
        except Exception as e:
            self.assertRaises(Exception, "Incorrect exception type due to passed neutral_zone_ids that contains a string that is not a number as part of a set")


    def test__segment_of_the_week__load_segment__whenCalledWithValidSegment__populatesSegmentData(self):
        sotw = SegmentOfTheWeek(2016, 30, 6216534, set([12721002, 12745854]))

        sotw.update_efforts()
        sotw.enrich_efforts()

        self.assertIsNotNone(sotw.segment_efforts)


    def setup_test_data(self):
        this_year, this_week_number = self.get_current_year_and_week_number()

        redisclient.delete('sotw_2016_01_segment')
        redisclient.delete('sotw_2016_01_neutral_zones')

        redisclient.delete('sotw_2016_03_segment')
        redisclient.delete('sotw_2016_03_neutral_zones')

        redisclient.delete('sotw_%s_%s_segment' % (this_year, this_week_number))
        redisclient.delete('sotw_%s_%s_neutral_zones' % (this_year, this_week_number))

        redisclient.set('sotw_2016_01_segment', 6784576)
        redisclient.sadd('sotw_2016_01_neutral_zones', 768320468)
        redisclient.sadd('sotw_2016_01_neutral_zones', 7097863)


    def get_current_year_and_week_number(self):
        return date.today().year, date.today().isocalendar()[1]


if __name__ == "__main__":
    unittest.main()