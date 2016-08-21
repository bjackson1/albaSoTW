from strava import Strava
from storage import redisclient

class Athlete:
    def __init__(self, athlete_id, firstname=None, lastname=None, gender=None, clubs=[]):
        self.id = athlete_id
        self.firstname = firstname
        self.lastname = lastname
        self.gender = gender
        self.clubs = clubs

        self.load()


    def load(self):
        raw_data = redisclient.hgetall(self.id)
        to_save = False

        if raw_data == {}:
            raw_data = self.get_from_strava()
            to_save = True

        self.load_data(raw_data)

        if to_save:
            self.save()


    def get_from_strava(self):
        self.load_data(Strava().get_athlete(self.id))


    def load_data(self, raw_data):
        if raw_data != None:
            if 'clubs' in raw_data:
                self.clubs = raw_data['clubs']

            if 'sex' in raw_data:
                self.gender = raw_data['sex']

            if 'gender' in raw_data:
                self.gender = raw_data['gender']

            if 'firstname' in raw_data:
                self.firstname = raw_data['firstname']

            if 'lastname' in raw_data:
                self.lastname = raw_data['lastname']


    def save(self):
        redisclient.hset(self.id, 'gender', self.gender)
        redisclient.hset(self.id, 'firstname', self.firstname)
        redisclient.hset(self.id, 'lastname', self.lastname)
        redisclient.hset(self.id, 'clubs', self.clubs)
