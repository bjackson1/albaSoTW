from strava import Strava
from storage import redisclient

class Athlete:
    def __init__(self, athlete_id):
        self.athlete_id = athlete_id

        self.get_from_redis()

        if not self.athlete_object:
            self.get_from_strava()
            self.set_in_redis()
            self.get_from_redis()

        self.athlete_object['id'] = self.athlete_id

    def get(self):
        return self.athlete_object

    def get_from_redis(self):
        self.athlete_object = redisclient.hgetall(self.athlete_id)

    def get_from_strava(self):
        self.athlete_object = Strava().get_athlete(self.athlete_id)

    def set_in_redis(self):
        redisclient.hset(self.athlete_id, 'sex', self.athlete_object['sex'])
        redisclient.hset(self.athlete_id, 'firstname', self.athlete_object['firstname'])
        redisclient.hset(self.athlete_id, 'lastname', self.athlete_object['lastname'])

        if 'clubs' in self.athlete_object:
            redisclient.hset(self.athlete_id, 'clubs', self.athlete_object['clubs'])
