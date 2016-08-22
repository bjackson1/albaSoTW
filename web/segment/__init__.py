from strava import Strava
from storage import redisclient

class Segment:
    def __init__(self, segment_id):
        self.id = segment_id
        self.key_name = 'segment_%s' % self.id
        self.load()


    def load(self):
        raw_data = redisclient.hgetall(self.key_name)
        to_save = False

        if raw_data == {}:
            raw_data = self.get_from_strava()
            to_save = True

        self.load_data(raw_data)

        if to_save:
            self.save()


    def load_data(self, raw_data):
        if raw_data != None:
            if 'name' in raw_data:
                self.name = raw_data['name']

            if 'distance' in raw_data:
                self.distance = float(raw_data['distance'])

            if 'total_elevation_gain' in raw_data:
                self.total_elevation_gain = float(raw_data['total_elevation_gain'])


    def get_from_strava(self):
        return Strava().get_segment(self.id)


    def save(self):
        redisclient.hset(self.key_name, 'name', self.name)
        redisclient.hset(self.key_name, 'distance', self.distance)
        redisclient.hset(self.key_name, 'total_elevation_gain', self.total_elevation_gain)
