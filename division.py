from strava import Strava
from storage import redisclient
from athlete import Athlete

class Division:
    # division_id = None
    # division_object = {}

    def __init__(self, division_id):
        self.division_id = division_id

        self.get_from_redis()

    def get(self):
        return self.division_object

    def add_athlete(self, athlete_id):
        redisclient.sadd('%s_members' % self.division_id, athlete_id)

    def get_from_redis(self):
        self.division_object = {}
        self.division_object['id'] = self.division_id
        self.division_object['name'] = redisclient.hget(self.division_id, 'name')
        self.division_object['members'] = {}

        for member in redisclient.smembers('%s_members' % self.division_id):
            self.division_object['members'][member] = {}
            self.division_object['members'][member]['id'] = member

    @staticmethod
    def get_all(get_athletes=False):
        divisions = {}

        division_list = redisclient.smembers('divisions')
        print(division_list)

        for division_id in division_list:
            division = Division(division_id).get()

            if get_athletes:
                for member in division['members']:
                    division['members'][member] = Athlete(member).get()

            divisions[division_id] = division

        return divisions
