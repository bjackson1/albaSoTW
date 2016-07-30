from strava import Strava
from storage import redisclient

class Segment:
    def __init__(self, segment_id):
        self.segment_id = segment_id
        self.redis_key = 'segment_%s' % segment_id

        self.get_from_redis()

        if not self.segment_object:
            self.get_from_strava()
            self.set_in_redis()
            self.get_from_redis()

        self.segment_object['id'] = self.segment_id

    def get(self):
        return self.segment_object

    def get_from_redis(self):
        self.segment_object = redisclient.hgetall(self.redis_key)

    def get_from_strava(self):
        self.segment_object = Strava().get_segment(self.segment_id)

    def set_in_redis(self):
        redisclient.hset(self.redis_key, 'name', self.segment_object['name'])
        redisclient.hset(self.redis_key, 'distance', self.segment_object['distance'])
        redisclient.hset(self.redis_key, 'total_elevation_gain', self.segment_object['total_elevation_gain'])
