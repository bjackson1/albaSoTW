import unittest
from datetime import date, datetime
from storage import redisclient
import mock
from segment_of_the_week import SegmentOfTheWeek

class tests_SegmentOfTheWeek(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        redisclient('localhost', 6379, db=1)
        super(tests_SegmentOfTheWeek, self).__init__(*args, **kwargs)
        # self.setup_test_data()
        self.test_instance = SegmentOfTheWeek()


    def test__segment_of_the_week__get_all__whenCalledWithMockData__returnsAllSegmentOfTheWeekChallenges(self):
        keys = redisclient.keys('sotw_*')

        for key in keys:
            redisclient.delete(key)

        for i in range(1, 31):
            key_name = '%s_%02d' % (2016, i)
            redisclient.delete('%s_results' % key_name)
            redisclient.delete('sotw_%s_segment' % key_name)
            redisclient.delete('sotw_%s_neutral_zones' % key_name)

            redisclient.delete('segment_1%04d' % i)
            redisclient.delete('segment_2%04d' % i)
            redisclient.delete('segment_3%04d' % i)

            redisclient.set('sotw_%s_segment' % key_name, 10000 + i)
            redisclient.sadd('sotw_%s_neutral_zones' % key_name, 20000 + i)
            redisclient.sadd('sotw_%s_neutral_zones' % key_name, 30000 + i)

            for j in range(1, 4):
                redisclient.hset('segment_%s%04d' % (j, i), 'name', 'Test Segment %s%04d' % (j, i))
                redisclient.hset('segment_%s%04d' % (j, i), 'distance', 1000)
                redisclient.hset('segment_%s%04d' % (j, i), 'total_elevation_gain', 100)

        challenges = SegmentOfTheWeek.get_all_challenges_data()
        self.assertTrue(len(challenges) >= 30)


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
        self.setup_test_data()
        expected_segment_id = 6784576
        expected_neutral_zone_ids = {7097863, 768320468}

        sotw = SegmentOfTheWeek(2016, 1)

        self.assertEqual(sotw.main_segment_id, expected_segment_id)
        self.assertEqual(sotw.neutral_zone_ids, expected_neutral_zone_ids)


    def test__segment_of_the_week__get_segment_ids__whenCalledWithYearAndWeekNumberWithUnpopulatedData__returnsNoneAndEmptySet(self):
        self.setup_test_data()
        sotw = SegmentOfTheWeek(2016, 3)

        self.assertEqual(sotw.main_segment_id, None)
        self.assertEqual(sotw.neutral_zone_ids, set())


    def test__segment_of_the_week__init__whenCalledWithDefinedAndPopulatedYearAndWeekNumber__setsUpObjectWithDefinedValues(self):
        self.setup_test_data()
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
        self.setup_test_data()
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


    def test__segment_of_the_week__init__whenCalledWithValidValues__throwsException(self):
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


    def test__segment_of_the_week__load_segment__whenCalledWithMockedSegment__populatesSegmentData(self):
        sotw = SegmentOfTheWeek(2016, 30, 6216534)

        with mock.patch('strava.Strava.get_efforts') as mock_strava:
            mock_strava.return_value = [{"id": "123456", "activity": {"id": "234567"}, "elapsed_time": 1200, "distance": 10000}]

            sotw.update_efforts()

        self.assertIsNotNone(sotw.segment_efforts, "segment_efforts Dict is not populated")
        self.assertTrue("234567" in sotw.segment_efforts, "segment_efforts Dict does not contain the expected mocked element '234567'")
        self.assertEqual(sotw.segment_efforts["234567"]['elapsed_time'], 1200, "segment_efforts Dict element '234567' does not have the correct value for the elapsed_time property")


    def test__segment_of_the_week__load_segment__whenCalledWithMockedSegment__populatesAndEnrichesSegmentData(self):
        sotw = SegmentOfTheWeek(2016, 30, 6216534)

        with mock.patch('strava.Strava.get_efforts') as mock_strava:
            mock_strava.return_value = [{"id": "123456", "activity": {"id": "234567"}, "elapsed_time": 1200, "distance": 10000, 'start_date_local': '2016-06-20T20:00:00Z'}]

            sotw.update_efforts()
            sotw.enrich_efforts()

        self.assertTrue("pace_kph" in sotw.segment_efforts['234567'], "segment_effort['234567'] Dict does not contain the expected mocked element 'pace_kph'")
        self.assertTrue("pace_mph" in sotw.segment_efforts['234567'], "segment_effort['234567'] Dict does not contain the expected mocked element 'pace_mph'")
        self.assertTrue("net_elapsed_time" in sotw.segment_efforts['234567'], "segment_effort['234567'] Dict does not contain the expected mocked element 'net_elapsed_time'")
        self.assertTrue("neutralised_times" in sotw.segment_efforts['234567'], "segment_effort['234567'] Dict does not contain the expected mocked element 'neutralised_times'")

        self.assertEqual(sotw.segment_efforts['234567']['pace_kph'], 30.0)
        self.assertEqual(sotw.segment_efforts['234567']['pace_mph'], 18.63)
        self.assertEqual(sotw.segment_efforts['234567']['net_elapsed_time'], 1200)
        self.assertEqual(sotw.segment_efforts['234567']['neutralised_times'], [])


    def test__segment_of_the_week__load_segment__whenCalledWithMockedSegmentAndSingleNeutralisedZone__populatesAndEnrichesSegmentDataAndDeductsNeutralTimes(self):
        sotw = SegmentOfTheWeek(2016, 30, 6216534, set([345678]))

        with mock.patch('strava.Strava.get_efforts') as mock_get_efforts, \
                mock.patch('strava.Strava.get_neutralised_efforts') as mock_get_neutralised_efforts:
            mock_get_efforts.return_value = [{"id": "123456", "activity": {"id": "234567"}, "elapsed_time": 1200, "distance": 10000, 'start_date_local': '2016-06-20T20:00:00Z'}]
            mock_get_neutralised_efforts.return_value = [{"id": "1234567", "activity": {"id": "234567"}, "elapsed_time": 12, "distance": 100, 'start_date_local': '2016-06-20T20:01:00Z'}]

            sotw.update_efforts()
            sotw.enrich_efforts()

        self.assertTrue("pace_kph" in sotw.segment_efforts['234567'], "segment_effort['234567'] Dict does not contain the expected mocked element 'pace_kph'")
        self.assertTrue("pace_mph" in sotw.segment_efforts['234567'], "segment_effort['234567'] Dict does not contain the expected mocked element 'pace_mph'")
        self.assertTrue("net_elapsed_time" in sotw.segment_efforts['234567'], "segment_effort['234567'] Dict does not contain the expected mocked element 'net_elapsed_time'")
        self.assertTrue("neutralised_times" in sotw.segment_efforts['234567'], "segment_effort['234567'] Dict does not contain the expected mocked element 'neutralised_times'")

        self.assertEqual(sotw.segment_efforts['234567']['pace_kph'], 30.0)
        self.assertEqual(sotw.segment_efforts['234567']['pace_mph'], 18.63)
        self.assertEqual(sotw.segment_efforts['234567']['net_elapsed_time'], 1188)
        self.assertEqual(sotw.segment_efforts['234567']['neutralised_times'], [12])


    def test__segment_of_the_week__load_segment__whenCalledWithMockedSegmentAndMultipleNeutralisedZones__populatesAndEnrichesSegmentDataAndDeductsNeutralTimes(self):
        sotw = SegmentOfTheWeek(2016, 30, 6216534, set([345678, 456789]))

        with mock.patch('strava.Strava.get_efforts') as mock_get_efforts, \
                mock.patch('strava.Strava.get_neutralised_efforts') as mock_get_neutralised_efforts:
            mock_get_efforts.return_value = [{"id": "123456", "activity": {"id": "234567"}, "elapsed_time": 1200, "distance": 10000, 'start_date_local': '2016-06-20T20:00:00Z'}]

            # Given that this is mocked and there are two 'pretend' neutralised segments specified in the SegmentOfTheWeek instantiator, we can
            #   expect each neutralised segment here to be counted twice for each given effort
            mock_get_neutralised_efforts.return_value = [{"id": "1234567", "activity": {"id": "234567"}, "elapsed_time": 12, "distance": 100, 'start_date_local': '2016-06-20T20:01:00Z'}]

            sotw.update_efforts()
            sotw.enrich_efforts()

        self.assertTrue("pace_kph" in sotw.segment_efforts['234567'], "segment_effort['234567'] Dict does not contain the expected mocked element 'pace_kph'")
        self.assertTrue("pace_mph" in sotw.segment_efforts['234567'], "segment_effort['234567'] Dict does not contain the expected mocked element 'pace_mph'")
        self.assertTrue("net_elapsed_time" in sotw.segment_efforts['234567'], "segment_effort['234567'] Dict does not contain the expected mocked element 'net_elapsed_time'")
        self.assertTrue("neutralised_times" in sotw.segment_efforts['234567'], "segment_effort['234567'] Dict does not contain the expected mocked element 'neutralised_times'")

        self.assertEqual(sotw.segment_efforts['234567']['pace_kph'], 30.0)
        self.assertEqual(sotw.segment_efforts['234567']['pace_mph'], 18.63)
        self.assertEqual(sotw.segment_efforts['234567']['net_elapsed_time'], 1176)
        self.assertEqual(sotw.segment_efforts['234567']['neutralised_times'], [12, 12])


    def test__segment_of_the_week__load_segment__whenCalledWithMockedSegmentAndMultipleNeutralisedZonesWithOneOutsideEffortTime__populatesAndEnrichesSegmentDataAndDeductsNeutralTimesExcludingDuplicateEffort(self):
        sotw = SegmentOfTheWeek(2016, 30, 6216534, set([345678]))

        with mock.patch('strava.Strava.get_efforts') as mock_get_efforts, \
                mock.patch('strava.Strava.get_neutralised_efforts') as mock_get_neutralised_efforts:
            mock_get_efforts.return_value = [{"id": "123456", "activity": {"id": "234567"}, "elapsed_time": 1200, "distance": 10000, 'start_date_local': '2016-06-20T20:00:00Z'}]

            # Given that this is mocked and there are two 'pretend' neutralised segments specified in the SegmentOfTheWeek instantiator, we can
            #   expect each neutralised segment here to be counted twice for each given effort
            mock_get_neutralised_efforts.return_value = [{"id": "1234567", "activity": {"id": "234567"}, "elapsed_time": 12, "distance": 100, 'start_date_local': '2016-06-20T20:05:00Z'},
                                                         {"id": "1234569", "activity": {"id": "234567"}, "elapsed_time": 12, "distance": 100, 'start_date_local': '2016-06-20T20:25:00Z'}]

            sotw.update_efforts()
            sotw.enrich_efforts()

        self.assertTrue("pace_kph" in sotw.segment_efforts['234567'], "segment_effort['234567'] Dict does not contain the expected mocked element 'pace_kph'")
        self.assertTrue("pace_mph" in sotw.segment_efforts['234567'], "segment_effort['234567'] Dict does not contain the expected mocked element 'pace_mph'")
        self.assertTrue("net_elapsed_time" in sotw.segment_efforts['234567'], "segment_effort['234567'] Dict does not contain the expected mocked element 'net_elapsed_time'")
        self.assertTrue("neutralised_times" in sotw.segment_efforts['234567'], "segment_effort['234567'] Dict does not contain the expected mocked element 'neutralised_times'")

        self.assertEqual(sotw.segment_efforts['234567']['pace_kph'], 30.0)
        self.assertEqual(sotw.segment_efforts['234567']['pace_mph'], 18.63)
        # self.assertEqual(sotw.segment_efforts['234567']['net_elapsed_time'], 1188)
        self.assertEqual(sotw.segment_efforts['234567']['neutralised_times'], [12])


    def test__segment_of_the_week__load_segment__whenCalledWithMockedSegmentAndMultipleEffortsAndNeutralisedZones__populatesAndEnrichesSegmentDataAndDeductsNeutralTimes(self):
        sotw = SegmentOfTheWeek(2016, 30, 6216534, set([345678, 456789]))

        with mock.patch('strava.Strava.get_efforts') as mock_get_efforts, \
                mock.patch('strava.Strava.get_neutralised_efforts') as mock_get_neutralised_efforts:
            mock_get_efforts.return_value = [{"id": "123456", "activity": {"id": "234567"}, "elapsed_time": 1200, "distance": 10000, 'start_date_local': '2016-06-20T20:00:00Z'},
                                             {"id": "123457", "activity": {"id": "234568"}, "elapsed_time": 1200, "distance": 10000, 'start_date_local': '2016-06-20T20:00:00Z'},
                                             {"id": "123458", "activity": {"id": "234569"}, "elapsed_time": 1200, "distance": 10000, 'start_date_local': '2016-06-20T20:00:00Z'}]

            # Given that this is mocked and there are two 'pretend' neutralised segments specified in the SegmentOfTheWeek instantiator, we can
            #   expect each neutralised segment here to be counted twice for each given effort
            mock_get_neutralised_efforts.return_value = [{"id": "1234567", "activity": {"id": "234567"}, "elapsed_time": 12, "distance": 100, 'start_date_local': '2016-06-20T20:01:00Z'},
                                                         {"id": "1234567", "activity": {"id": "234568"}, "elapsed_time": 24, "distance": 100, 'start_date_local': '2016-06-20T20:01:00Z'},
                                                         {"id": "1234567", "activity": {"id": "234569"}, "elapsed_time": 48, "distance": 100, 'start_date_local': '2016-06-20T20:01:00Z'}]

            sotw.update_efforts()
            sotw.enrich_efforts()

        self.assertTrue("234567" in sotw.segment_efforts, "segment_effort['234567'] does not exist")
        self.assertTrue("234568" in sotw.segment_efforts, "segment_effort['234568'] does not exist")
        self.assertTrue("234569" in sotw.segment_efforts, "segment_effort['234569'] does not exist")

        self.assertEqual(sotw.segment_efforts['234567']['pace_kph'], 30.0)
        self.assertEqual(sotw.segment_efforts['234567']['pace_mph'], 18.63)
        self.assertEqual(sotw.segment_efforts['234567']['net_elapsed_time'], 1176)
        self.assertEqual(sotw.segment_efforts['234567']['neutralised_times'], [12, 12])

        self.assertEqual(sotw.segment_efforts['234568']['pace_kph'], 30.62)
        self.assertEqual(sotw.segment_efforts['234568']['pace_mph'], 19.02)
        self.assertEqual(sotw.segment_efforts['234568']['net_elapsed_time'], 1152)
        self.assertEqual(sotw.segment_efforts['234568']['neutralised_times'], [24, 24])

        self.assertEqual(sotw.segment_efforts['234569']['pace_kph'], 31.96)
        self.assertEqual(sotw.segment_efforts['234569']['pace_mph'], 19.85)
        self.assertEqual(sotw.segment_efforts['234569']['net_elapsed_time'], 1104)
        self.assertEqual(sotw.segment_efforts['234569']['neutralised_times'], [48, 48])


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


    def test__segment_of_the_week__compile_results_table__whenCalledWithSegmentOfTheWeekAndSingleEffort_returnsTableWithRankedEffort(self):
        from division import Division
        sotw = SegmentOfTheWeek(2016, 30, 6216534, set([345678, 456789]))

        with mock.patch('strava.Strava.get_efforts') as mock_get_efforts, \
                mock.patch('strava.Strava.get_neutralised_efforts') as mock_get_neutralised_efforts:

            mock_get_efforts.return_value = [
                {"id": "123456", "activity": {"id": "234567"}, "athlete": {"id": 10000002}, "elapsed_time": 1200, "distance": 10000, 'start_date_local': '2016-06-20T20:00:00Z'}]

            # Given that this is mocked and there are two 'pretend' neutralised segments specified in the SegmentOfTheWeek instantiator, we can
            #   expect each neutralised segment here to be counted twice for each given effort
            mock_get_neutralised_efforts.return_value = [
                {"id": "1234567", "activity": {"id": "234567"}, "elapsed_time": 12, "distance": 100, 'start_date_local': '2016-06-20T20:01:00Z'}]

            sotw.update_efforts()
            sotw.enrich_efforts()

            division = Division('tbotr')

            sotw.compile_results_table(division)
            results = sotw.results

            self.assertIsNotNone(results)
            self.assertEqual(results[division.id]['efforts'][10000002]['rank'], 1)
            self.assertEqual(results[division.id]['efforts'][10000002]['points'], 10)


    def test__segment_of_the_week__compile_results_table__whenCalledWithSegmentOfTheWeekAndMultipleEffortsFromSingleAthlete_returnsTableWithRankedEffort(self):
        from division import Division
        sotw = SegmentOfTheWeek(2016, 30, 6216534, set([345678, 456789]))

        with mock.patch('strava.Strava.get_efforts') as mock_get_efforts, \
                mock.patch('strava.Strava.get_neutralised_efforts') as mock_get_neutralised_efforts:

            mock_get_efforts.return_value = [
                {"id": "1234567", "activity": {"id": "2345678"}, "athlete": {"id": 10000002}, "elapsed_time": 1200, "distance": 10000, 'start_date_local': '2016-06-20T20:00:00Z'},
                {"id": "1234568", "activity": {"id": "2345679"}, "athlete": {"id": 10000002}, "elapsed_time": 1100, "distance": 10000, 'start_date_local': '2016-06-20T20:00:00Z'},
                {"id": "1234569", "activity": {"id": "2345670"}, "athlete": {"id": 10000002}, "elapsed_time": 1300, "distance": 10000, 'start_date_local': '2016-06-20T20:00:00Z'}]

            # Given that this is mocked and there are two 'pretend' neutralised segments specified in the SegmentOfTheWeek instantiator, we can
            #   expect each neutralised segment here to be counted twice for each given effort
            mock_get_neutralised_efforts.return_value = [
                {"id": "12345678", "activity": {"id": "2345678"}, "elapsed_time": 12, "distance": 100, 'start_date_local': '2016-06-20T20:01:00Z'},
                {"id": "12345679", "activity": {"id": "2345679"}, "elapsed_time": 12, "distance": 100, 'start_date_local': '2016-06-20T20:01:00Z'},
                {"id": "12345670", "activity": {"id": "2345670"}, "elapsed_time": 12, "distance": 100, 'start_date_local': '2016-06-20T20:01:00Z'}]

            sotw.update_efforts()
            sotw.enrich_efforts()

            division = Division('tbotr')

            sotw.compile_results_table(division)
            results = sotw.results

            self.assertIsNotNone(results)
            self.assertEqual(results[division.id]['efforts'][10000002]['rank'], 1)
            self.assertEqual(results[division.id]['efforts'][10000002]['points'], 10)


    def test__segment_of_the_week__compile_results_table__whenCalledWithSegmentOfTheWeekAndMultipleEffortsFromMultipleAthletes_returnsTableWithRankedEfforts(self):
        self.setup_test_data()
        from division import Division
        sotw = SegmentOfTheWeek(2016, 30, 6216534, set([345678, 456789]))

        with mock.patch('strava.Strava.get_efforts') as mock_get_efforts, \
                mock.patch('strava.Strava.get_neutralised_efforts') as mock_get_neutralised_efforts:

            mock_get_efforts.return_value = [
                {"id": "1234565", "activity": {"id": "2345676"}, "athlete": {"id": 10000001}, "elapsed_time": 1100, "distance": 10000, 'start_date_local': '2016-06-20T20:00:00Z'},
                {"id": "1234566", "activity": {"id": "2345677"}, "athlete": {"id": 10000003}, "elapsed_time": 1050, "distance": 10000, 'start_date_local': '2016-06-20T20:00:00Z'},
                {"id": "1234567", "activity": {"id": "2345678"}, "athlete": {"id": 10000002}, "elapsed_time": 1200, "distance": 10000, 'start_date_local': '2016-06-20T20:00:00Z'},
                {"id": "1234568", "activity": {"id": "2345679"}, "athlete": {"id": 10000002}, "elapsed_time": 1100, "distance": 10000, 'start_date_local': '2016-06-20T20:00:00Z'},
                {"id": "1234569", "activity": {"id": "2345670"}, "athlete": {"id": 10000002}, "elapsed_time": 1300, "distance": 10000, 'start_date_local': '2016-06-20T20:00:00Z'},
                {"id": "1234560", "activity": {"id": "2345671"}, "athlete": {"id": 10000004}, "elapsed_time": 1400, "distance": 10000, 'start_date_local': '2016-06-20T20:00:00Z'}]

            # Given that this is mocked and there are two 'pretend' neutralised segments specified in the SegmentOfTheWeek instantiator, we can
            #   expect each neutralised segment here to be counted twice for each given effort
            mock_get_neutralised_efforts.return_value = [
                {"id": "12345676", "activity": {"id": "2345676"}, "elapsed_time": 12, "distance": 100, 'start_date_local': '2016-06-20T20:01:00Z'},
                {"id": "12345677", "activity": {"id": "2345677"}, "elapsed_time": 12, "distance": 100, 'start_date_local': '2016-06-20T20:01:00Z'},
                {"id": "12345678", "activity": {"id": "2345678"}, "elapsed_time": 12, "distance": 100, 'start_date_local': '2016-06-20T20:01:00Z'},
                {"id": "12345679", "activity": {"id": "2345679"}, "elapsed_time": 12, "distance": 100, 'start_date_local': '2016-06-20T20:01:00Z'},
                {"id": "12345670", "activity": {"id": "2345670"}, "elapsed_time": 12, "distance": 100, 'start_date_local': '2016-06-20T20:01:00Z'},
                {"id": "12345671", "activity": {"id": "2345671"}, "elapsed_time": 12, "distance": 100, 'start_date_local': '2016-06-20T20:01:00Z'}]

            sotw.update_efforts()
            sotw.enrich_efforts()

            division = Division('tbotr')

            sotw.compile_results_table(division)
            results = sotw.results

            self.assertIsNotNone(results)
            self.assertEqual(results[division.id]['efforts'][10000001]['rank'], 2)
            self.assertEqual(results[division.id]['efforts'][10000001]['points'], 9)
            self.assertEqual(results[division.id]['efforts'][10000002]['rank'], 2)
            self.assertEqual(results[division.id]['efforts'][10000002]['points'], 9)
            self.assertEqual(results[division.id]['efforts'][10000003]['rank'], 1)
            self.assertEqual(results[division.id]['efforts'][10000003]['points'], 10)
            self.assertEqual(results[division.id]['efforts'][10000004]['rank'], 4)
            self.assertEqual(results[division.id]['efforts'][10000004]['points'], 7)


    def test__segment_of_the_week__compile_all_results__whenCalledWithFullyMockedData_returnsTableWithRankedEfforts(self):
        sotw = SegmentOfTheWeek(2016, 30, 6216534, set([345678, 456789]))

        redisclient.delete('divisions')

        for i in range(1, 5):
            div_id = 'tdiv%s' % i
            redisclient.delete(div_id)
            redisclient.delete('%s_members' % div_id)
            redisclient.hset(div_id, 'name', 'Division %s' % i)
            redisclient.sadd('divisions', div_id)


        test_athletes = [{'id': 3000, 'firstname': 'Athlete', 'lastname': '3000', 'division': 'tdiv1'},
                         {'id': 3001, 'firstname': 'Athlete', 'lastname': '3001', 'division': 'tdiv1'},
                         {'id': 3002, 'firstname': 'Athlete', 'lastname': '3002', 'division': 'tdiv1'},
                         {'id': 3003, 'firstname': 'Athlete', 'lastname': '3003', 'division': 'tdiv2'},
                         {'id': 3004, 'firstname': 'Athlete', 'lastname': '3004', 'division': 'tdiv2'},
                         {'id': 3005, 'firstname': 'Athlete', 'lastname': '3005', 'division': 'tdiv2'},
                         {'id': 3006, 'firstname': 'Athlete', 'lastname': '3006', 'division': 'tdiv2'},
                         {'id': 3007, 'firstname': 'Athlete', 'lastname': '3007', 'division': 'tdiv2'},
                         {'id': 3008, 'firstname': 'Athlete', 'lastname': '3008', 'division': 'tdiv3'},
                         {'id': 3009, 'firstname': 'Athlete', 'lastname': '3009', 'division': 'tdiv3'},
                         {'id': 3010, 'firstname': 'Athlete', 'lastname': '3010', 'division': 'tdiv3'},
                         {'id': 3011, 'firstname': 'Athlete', 'lastname': '3011', 'division': 'tdiv3'},
                         {'id': 3012, 'firstname': 'Athlete', 'lastname': '3012', 'division': 'tdiv3'},
                         {'id': 3013, 'firstname': 'Athlete', 'lastname': '3013', 'division': 'tdiv3'},
                         {'id': 3014, 'firstname': 'Athlete', 'lastname': '3014', 'division': 'tdiv3'},
                         {'id': 3015, 'firstname': 'Athlete', 'lastname': '3015', 'division': 'tdiv3'},
                         {'id': 3016, 'firstname': 'Athlete', 'lastname': '3016', 'division': 'tdiv4'},
                         {'id': 3017, 'firstname': 'Athlete', 'lastname': '3017', 'division': 'tdiv4'},
                         {'id': 3018, 'firstname': 'Athlete', 'lastname': '3018', 'division': 'tdiv4'},
                         {'id': 3019, 'firstname': 'Athlete', 'lastname': '3019', 'division': 'tdiv4'}]

        for athlete in test_athletes:
            redisclient.delete(athlete['id'])
            redisclient.hset(athlete['id'], 'firstname', athlete['firstname'])
            redisclient.hset(athlete['id'], 'lastname', athlete['lastname'])
            redisclient.sadd('%s_members' % athlete['division'], athlete['id'])

        with mock.patch('strava.Strava.get_efforts') as mock_get_efforts, \
                mock.patch('strava.Strava.get_neutralised_efforts') as mock_get_neutralised_efforts:

            mock_get_efforts.return_value = [
                {"id": "1000", "activity": {"id": "2000"}, "athlete": {"id": 3000}, "elapsed_time": 987, "distance": 10000, 'start_date_local': '2016-06-20T20:00:00Z'},
                {"id": "1001", "activity": {"id": "2001"}, "athlete": {"id": 3001}, "elapsed_time": 1102, "distance": 10000, 'start_date_local': '2016-06-20T20:00:00Z'},
                {"id": "1002", "activity": {"id": "2002"}, "athlete": {"id": 3002}, "elapsed_time": 1005, "distance": 10000, 'start_date_local': '2016-06-20T20:00:00Z'},
                {"id": "1003", "activity": {"id": "2003"}, "athlete": {"id": 3003}, "elapsed_time": 1007, "distance": 10000, 'start_date_local': '2016-06-20T20:00:00Z'},
                {"id": "1004", "activity": {"id": "2004"}, "athlete": {"id": 3004}, "elapsed_time": 1404, "distance": 10000, 'start_date_local': '2016-06-20T20:00:00Z'},
                {"id": "1005", "activity": {"id": "2005"}, "athlete": {"id": 3005}, "elapsed_time": 1200, "distance": 10000, 'start_date_local': '2016-06-20T20:00:00Z'},
                {"id": "1006", "activity": {"id": "2006"}, "athlete": {"id": 3006}, "elapsed_time": 1090, "distance": 10000, 'start_date_local': '2016-06-20T20:00:00Z'},
                {"id": "1007", "activity": {"id": "2007"}, "athlete": {"id": 3007}, "elapsed_time": 1040, "distance": 10000, 'start_date_local': '2016-06-20T20:00:00Z'},
                {"id": "1008", "activity": {"id": "2008"}, "athlete": {"id": 3008}, "elapsed_time": 1250, "distance": 10000, 'start_date_local': '2016-06-20T20:00:00Z'},
                {"id": "1009", "activity": {"id": "2009"}, "athlete": {"id": 3009}, "elapsed_time": 1600, "distance": 10000, 'start_date_local': '2016-06-20T20:00:00Z'},
                {"id": "1010", "activity": {"id": "2010"}, "athlete": {"id": 3010}, "elapsed_time": 1320, "distance": 10000, 'start_date_local': '2016-06-20T20:00:00Z'},
                {"id": "1011", "activity": {"id": "2011"}, "athlete": {"id": 3011}, "elapsed_time": 1230, "distance": 10000, 'start_date_local': '2016-06-20T20:00:00Z'},
                {"id": "1012", "activity": {"id": "2012"}, "athlete": {"id": 3012}, "elapsed_time": 1234, "distance": 10000, 'start_date_local': '2016-06-20T20:00:00Z'},
                {"id": "1013", "activity": {"id": "2013"}, "athlete": {"id": 3013}, "elapsed_time": 1100, "distance": 10000, 'start_date_local': '2016-06-20T20:00:00Z'},
                {"id": "1014", "activity": {"id": "2014"}, "athlete": {"id": 3014}, "elapsed_time": 1290, "distance": 10000, 'start_date_local': '2016-06-20T20:00:00Z'},
                {"id": "1015", "activity": {"id": "2015"}, "athlete": {"id": 3015}, "elapsed_time": 1350, "distance": 10000, 'start_date_local': '2016-06-20T20:00:00Z'},
                {"id": "1016", "activity": {"id": "2016"}, "athlete": {"id": 3016}, "elapsed_time": 1400, "distance": 10000, 'start_date_local': '2016-06-20T20:00:00Z'},
                {"id": "1017", "activity": {"id": "2017"}, "athlete": {"id": 3017}, "elapsed_time": 1220, "distance": 10000, 'start_date_local': '2016-06-20T20:00:00Z'},
                {"id": "1018", "activity": {"id": "2018"}, "athlete": {"id": 3018}, "elapsed_time": 1410, "distance": 10000, 'start_date_local': '2016-06-20T20:00:00Z'},
                {"id": "1019", "activity": {"id": "2019"}, "athlete": {"id": 3019}, "elapsed_time": 1500, "distance": 10000, 'start_date_local': '2016-06-20T20:00:00Z'},
                {"id": "1020", "activity": {"id": "2020"}, "athlete": {"id": 3020}, "elapsed_time": 1402, "distance": 10000, 'start_date_local': '2016-06-20T20:00:00Z'},
                {"id": "1021", "activity": {"id": "2021"}, "athlete": {"id": 3021}, "elapsed_time": 1450, "distance": 10000, 'start_date_local': '2016-06-20T20:00:00Z'},
                {"id": "1022", "activity": {"id": "2022"}, "athlete": {"id": 3022}, "elapsed_time": 1390, "distance": 10000, 'start_date_local': '2016-06-20T20:00:00Z'},
                {"id": "1023", "activity": {"id": "2023"}, "athlete": {"id": 3023}, "elapsed_time": 1260, "distance": 10000, 'start_date_local': '2016-06-20T20:00:00Z'},
                {"id": "1024", "activity": {"id": "2024"}, "athlete": {"id": 3024}, "elapsed_time": 1420, "distance": 10000, 'start_date_local': '2016-06-20T20:00:00Z'},
                {"id": "1025", "activity": {"id": "2025"}, "athlete": {"id": 3025}, "elapsed_time": 1190, "distance": 10000, 'start_date_local': '2016-06-20T20:00:00Z'}]

            # Given that this is mocked and there are two 'pretend' neutralised segments specified in the SegmentOfTheWeek instantiator, we can
            #   expect each neutralised segment here to be counted twice for each given effort
            mock_get_neutralised_efforts.return_value = [
                {"id": "1100", "activity": {"id": "2000"}, "athlete": {"id": 3000}, 'start_date_local': '2016-06-20T20:01:00Z', "elapsed_time": 10, "distance": 100},
                {"id": "1101", "activity": {"id": "2001"}, "athlete": {"id": 3001}, 'start_date_local': '2016-06-20T20:01:00Z', "elapsed_time": 70, "distance": 100},
                {"id": "1102", "activity": {"id": "2002"}, "athlete": {"id": 3002}, 'start_date_local': '2016-06-20T20:01:00Z', "elapsed_time": 30, "distance": 100},
                {"id": "1103", "activity": {"id": "2003"}, "athlete": {"id": 3003}, 'start_date_local': '2016-06-20T20:01:00Z', "elapsed_time": 112, "distance": 100},
                {"id": "1104", "activity": {"id": "2004"}, "athlete": {"id": 3004}, 'start_date_local': '2016-06-20T20:01:00Z', "elapsed_time": 17, "distance": 100},
                {"id": "1105", "activity": {"id": "2005"}, "athlete": {"id": 3005}, 'start_date_local': '2016-06-20T20:01:00Z', "elapsed_time": 14, "distance": 100},
                {"id": "1106", "activity": {"id": "2006"}, "athlete": {"id": 3006}, 'start_date_local': '2016-06-20T20:01:00Z', "elapsed_time": 109, "distance": 100},
                {"id": "1107", "activity": {"id": "2007"}, "athlete": {"id": 3007}, 'start_date_local': '2016-06-20T20:01:00Z', "elapsed_time": 23, "distance": 100},
                {"id": "1108", "activity": {"id": "2008"}, "athlete": {"id": 3008}, 'start_date_local': '2016-06-20T20:01:00Z', "elapsed_time": 26, "distance": 100},
                {"id": "1109", "activity": {"id": "2009"}, "athlete": {"id": 3009}, 'start_date_local': '2016-06-20T20:01:00Z', "elapsed_time": 73, "distance": 100},
                {"id": "1110", "activity": {"id": "2010"}, "athlete": {"id": 3010}, 'start_date_local': '2016-06-20T20:01:00Z', "elapsed_time": 44, "distance": 100},
                {"id": "1111", "activity": {"id": "2011"}, "athlete": {"id": 3011}, 'start_date_local': '2016-06-20T20:01:00Z', "elapsed_time": 105, "distance": 100},
                {"id": "1112", "activity": {"id": "2012"}, "athlete": {"id": 3012}, 'start_date_local': '2016-06-20T20:01:00Z', "elapsed_time": 67, "distance": 100},
                {"id": "1113", "activity": {"id": "2013"}, "athlete": {"id": 3013}, 'start_date_local': '2016-06-20T20:01:00Z', "elapsed_time": 81, "distance": 100},
                {"id": "1114", "activity": {"id": "2014"}, "athlete": {"id": 3014}, 'start_date_local': '2016-06-20T20:01:00Z', "elapsed_time": 20, "distance": 100},
                {"id": "1115", "activity": {"id": "2015"}, "athlete": {"id": 3015}, 'start_date_local': '2016-06-20T20:01:00Z', "elapsed_time": 50, "distance": 100},
                {"id": "1116", "activity": {"id": "2016"}, "athlete": {"id": 3016}, 'start_date_local': '2016-06-20T20:01:00Z', "elapsed_time": 100, "distance": 100},
                {"id": "1117", "activity": {"id": "2017"}, "athlete": {"id": 3017}, 'start_date_local': '2016-06-20T20:01:00Z', "elapsed_time": 192, "distance": 100},
                {"id": "1118", "activity": {"id": "2018"}, "athlete": {"id": 3018}, 'start_date_local': '2016-06-20T20:01:00Z', "elapsed_time": 3, "distance": 100},
                {"id": "1119", "activity": {"id": "2019"}, "athlete": {"id": 3019}, 'start_date_local': '2016-06-20T20:01:00Z', "elapsed_time": 90, "distance": 100},
                {"id": "1120", "activity": {"id": "2020"}, "athlete": {"id": 3020}, 'start_date_local': '2016-06-20T20:01:00Z', "elapsed_time": 34, "distance": 100},
                {"id": "1121", "activity": {"id": "2021"}, "athlete": {"id": 3021}, 'start_date_local': '2016-06-20T20:01:00Z', "elapsed_time": 17, "distance": 100},
                {"id": "1122", "activity": {"id": "2022"}, "athlete": {"id": 3022}, 'start_date_local': '2016-06-20T20:01:00Z', "elapsed_time": 58, "distance": 100},
                {"id": "1123", "activity": {"id": "2023"}, "athlete": {"id": 3023}, 'start_date_local': '2016-06-20T20:01:00Z', "elapsed_time": 62, "distance": 100},
                {"id": "1124", "activity": {"id": "2024"}, "athlete": {"id": 3024}, 'start_date_local': '2016-06-20T20:01:00Z', "elapsed_time": 11, "distance": 100},
                {"id": "1125", "activity": {"id": "2025"}, "athlete": {"id": 3025}, 'start_date_local': '2016-06-20T20:01:00Z', "elapsed_time": 94, "distance": 100}]

            sotw.update_all_results()

            # for division_id, table in sotw.results.items():
            #     for athlete_id, effort in table['efforts'].items():
            #         print('Division: %s, Athlete: %s, Rank: %s, Time: %s' % (division_id, athlete_id, effort['rank'], effort['net_elapsed_time']))

            self.assertEqual(sotw.results['tdiv1']['efforts'][3000]['rank'], 3)
            self.assertEqual(sotw.results['tdiv1']['efforts'][3001]['rank'], 2)
            self.assertEqual(sotw.results['tdiv1']['efforts'][3002]['rank'], 1)
            self.assertEqual(sotw.results['tdiv2']['efforts'][3003]['rank'], 1)
            self.assertEqual(sotw.results['tdiv2']['efforts'][3004]['rank'], 5)
            self.assertEqual(sotw.results['tdiv2']['efforts'][3005]['rank'], 4)
            self.assertEqual(sotw.results['tdiv2']['efforts'][3006]['rank'], 2)
            self.assertEqual(sotw.results['tdiv2']['efforts'][3007]['rank'], 3)
            self.assertEqual(sotw.results['tdiv3']['efforts'][3008]['rank'], 4)
            self.assertEqual(sotw.results['tdiv3']['efforts'][3009]['rank'], 8)
            self.assertEqual(sotw.results['tdiv3']['efforts'][3010]['rank'], 5)
            self.assertEqual(sotw.results['tdiv3']['efforts'][3011]['rank'], 2)
            self.assertEqual(sotw.results['tdiv3']['efforts'][3012]['rank'], 3)
            self.assertEqual(sotw.results['tdiv3']['efforts'][3013]['rank'], 1)
            self.assertEqual(sotw.results['tdiv3']['efforts'][3014]['rank'], 6)
            self.assertEqual(sotw.results['tdiv3']['efforts'][3015]['rank'], 6)
            self.assertEqual(sotw.results['tdiv4']['efforts'][3016]['rank'], 2)
            self.assertEqual(sotw.results['tdiv4']['efforts'][3017]['rank'], 1)
            self.assertEqual(sotw.results['tdiv4']['efforts'][3018]['rank'], 4)
            self.assertEqual(sotw.results['tdiv4']['efforts'][3019]['rank'], 3)


    # def test__wibble(self):
    #     from division import Division
    #     redisclient('localhost', 6379)
    #     sotw = SegmentOfTheWeek(2016, 30)
    #
    #     sotw.update_efforts()
    #     sotw.enrich_efforts()
    #
    #     sotw.compile_all_results()
    #     sotw.load_all_results()
    #
    #     for division_id, table in sotw.results.items():
    #         for athlete_id, effort in table.items():
    #             print('Division: %s, Athlete: %s, Rank: %s, Time: %s' % (division_id, athlete_id, effort['rank'], effort['net_elapsed_time']))
    #
    #     print(sotw)

