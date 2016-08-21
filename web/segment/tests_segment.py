import unittest
from storage import redisclient
from load_data import loader
from segment import Segment
import mock


class tests_Segment(unittest.TestCase):
    test_data = None

    def setupTestData(self):
        redisclient('localhost', 6379, db=1)
        self.test_data = loader().setupTestData(file='../test_seed_data.yml')
        # self.efforts = self.test_data['loaded_efforts']

    def test_Segment_init_whenCalledWithSegmentIdNotInRedis_returnsSegmentRecordRetrievedFromStrava(self):
        with mock.patch('webrequest.getjsonfromurl') as mock_geturl:
            self.setupTestData()
            segment_id = 123456
            mock_geturl.return_value = self.test_data['segments'][segment_id]

            redis_key = 'segment_%s' % segment_id

            redisclient.delete(redis_key)
            segment = Segment(segment_id).get()

            mock_geturl.assert_called()

            self.assertEqual(segment['name'], 'Test Segment 1')
            self.assertEqual(segment['distance'], '1000')
            self.assertEqual(segment['total_elevation_gain'], '100')

    def test_Segment_whenCalledWithSegmentIdInRedis_returnsSegmentRecordFromRedis(self):
        with mock.patch('webrequest.getjsonfromurl') as mock_geturl:
            self.setupTestData()
            segment_id = 123456
            mock_geturl.return_value = self.test_data['segments'][segment_id]

            redis_key = 'segment_%s' % segment_id

            segment = Segment(segment_id).get()

            mock_geturl.assert_not_called()

            self.assertEqual(segment['name'], 'Test Segment 1')
            self.assertEqual(segment['distance'], '1000')
            self.assertEqual(segment['total_elevation_gain'], '100')
