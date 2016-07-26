from strava import Strava
from storage import redisclient
from athlete import Athlete

class Division:
    def __init__(self, division_id):
        self.division_id = division_id
        self.get_from_redis()
        # self.sex = self.division_object['sex']
        # self.name = self.division_object['name']

    def get(self):
        return self.division_object

    def add_athlete(self, athlete_id):
        athlete = Athlete(athlete_id).get()

        if athlete['sex'] == self.division_object['sex'] or athlete['sex'] == 'None':
            Division.remove_athlete_from_all_divisions(athlete_id)
            redisclient.sadd('%s_members' % self.division_id, athlete_id)

            return True
        else:
            return False

    @staticmethod
    def remove_athlete_from_division(division_id, athlete_id):
        redisclient.srem('%s_members' % division_id, athlete_id)

    @staticmethod
    def remove_athlete_from_all_divisions(athlete_id):
        for division_id in Division.get_all(False):
            Division.remove_athlete_from_division(division_id, athlete_id)

    def get_from_redis(self):
        self.division_object = {}
        self.division_object['id'] = self.division_id
        self.division_object['sex'] = redisclient.hget(self.division_id, 'sex')
        self.division_object['name'] = redisclient.hget(self.division_id, 'name')
        self.division_object['members'] = {}

        for member in redisclient.smembers('%s_members' % self.division_id):
            self.division_object['members'][member] = {}
            self.division_object['members'][member]['id'] = member

    @staticmethod
    def get_all(get_athletes=False):
        divisions = {}
        division_list = Division.get_list()

        for division_id in division_list:
            division = Division(division_id).get()

            if get_athletes:
                for member in division['members']:
                    division['members'][member] = Athlete(member).get()

            divisions[division_id] = division

        return divisions

    @staticmethod
    def get_list():
        return redisclient.smembers('divisions')