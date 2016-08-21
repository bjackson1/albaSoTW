from storage import redisclient
from athlete import Athlete


class Division:
    def __init__(self, division_id):
        self.id = division_id
        self.load()


    def add_athlete(self, athlete_id):
        Division.remove_athlete_from_all_divisions(athlete_id)
        redisclient.sadd('%s_members' % self.id, athlete_id)
        return True


    def remove_athlete(self, athlete_id):
        redisclient.srem('%s_members' % self.id, athlete_id)


    def load(self):
        self.gender = redisclient.hget(self.id, 'gender')
        self.name = redisclient.hget(self.id, 'name')
        self.members = {}

        for member in redisclient.smembers('%s_members' % self.id):
            if (type(member) is str and member.isdigit()):
                member_id = int(member)
                self.members[member_id] = Athlete(member_id)


    @staticmethod
    def remove_athlete_from_all_divisions(athlete_id):
        for division_id in Division.get_all():
            Division(division_id).remove_athlete(athlete_id)


    @staticmethod
    def get_all():
        divisions = {}
        division_list = Division.get_list()

        for division_id in division_list:
            division = Division(division_id)

            divisions[division_id] = division

        return divisions


    @staticmethod
    def get_list():
        return redisclient.smembers('divisions')