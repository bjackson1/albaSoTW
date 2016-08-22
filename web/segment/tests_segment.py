import unittest
from storage import redisclient
from segment import Segment
import mock


class tests_Segment(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        redisclient('localhost', 6379, db=1)
        super(tests_Segment, self).__init__(*args, **kwargs)


    def test_Segment_init_whenCalledWithSegmentIdNotInRedis_returnsSegmentRecordRetrievedFromStrava(self):
        with mock.patch('webrequest.getjsonfromurl') as mock_geturl:
            segment_id = 123456
            mock_geturl.return_value = {'distance': 1000.8, 'name': 'Test Segment 1', 'total_elevation_gain': 100.2}

            redis_key = 'segment_%s' % segment_id

            redisclient.delete(redis_key)
            segment = Segment(segment_id)

            mock_geturl.assert_called()

            self.assertEqual(segment.name, 'Test Segment 1')
            self.assertEqual(segment.distance, 1000.8)
            self.assertEqual(segment.total_elevation_gain, 100.2)


    def test_Segment_whenCalledWithSegmentIdInRedis_returnsSegmentRecordFromRedis(self):
        with mock.patch('webrequest.getjsonfromurl') as mock_geturl:
            segment_id = 123456
            segment_data =  {'distance': 1000.8, 'name': 'Test Segment 1', 'total_elevation_gain': 100.2}
            mock_geturl.return_value = segment_data

            redis_key = 'segment_%s' % segment_id
            redisclient.hset(redis_key, 'name', segment_data['name'])
            redisclient.hset(redis_key, 'distance', segment_data['distance'])
            redisclient.hset(redis_key, 'total_elevation_gain', segment_data['total_elevation_gain'])

            segment = Segment(segment_id)

            mock_geturl.assert_not_called()

            self.assertEqual(segment.name, 'Test Segment 1')
            self.assertEqual(segment.distance, 1000.8)
            self.assertEqual(segment.total_elevation_gain, 100.2)
