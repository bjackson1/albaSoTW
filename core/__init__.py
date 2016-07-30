import yaml
import os
from datetime import date, timedelta, datetime
from collections import OrderedDict

from storage import redisclient
from strava import Strava
from athlete import Athlete

SCRIPTPATH=os.path.dirname(os.path.realpath(__file__))


class AlbaSotwCore:
    __instance = None

    def __init__(self):
        self.config = self.load_config()

    def get():
        if AlbaSotwCore.__instance == None:
            AlbaSotwCore.__instance = AlbaSotwCore()

        return AlbaSotwCore.__instance

    def load_config(self):
        with open(SCRIPTPATH + '/../config.yml') as cfgstream:
            config = yaml.load(cfgstream)
            return config

    def add_sotw(self, segment_id, neutral_zones=None):
        key_name = self.get_sotw_key_name()
        redisclient.set('%s_segment' % key_name, segment_id)

        if neutral_zones != None:
            for neutral_zone in neutral_zones:
                redisclient.sadd('%s_neutral_zones' % key_name, neutral_zone)

    def get_sotw_key_name(self, year=None, week_number=None):
        today = date.today()

        if year == None:
            year = today.year

        if week_number == None:
            week_number = today.isocalendar()[1]

        return 'sotw_%s_%s' % (year, week_number)

    def compile_efforts(self):
        # access_token = redisclient.getasstring('api_token')
        key_name = self.get_sotw_key_name()
        segment = redisclient.get('%s_segment' % key_name)
        neutral_zones = redisclient.smembers('%s_neutral_zones' % key_name)

        leagues = {}

        today = date.today()
        starttime = datetime.combine(today - timedelta(today.weekday()), datetime.min.time())
        endtime = starttime + timedelta(days=5, hours=20)

        segment_efforts = Strava().get_efforts(segment, starttime, endtime)

        for segment_effort in segment_efforts:
            segment_effort['neutralised'] = {}

        for neutral_zone in neutral_zones:
            neutral_zone_efforts = Strava().get_efforts(neutral_zone, starttime, endtime)

            for neutral_zone_effort in neutral_zone_efforts:
                for segment_effort in segment_efforts:
                    if neutral_zone_effort['activity']['id'] == segment_effort['activity']['id']:
                        segment_effort['neutralised'][neutral_zone] = neutral_zone_effort['elapsed_time']

        divisions = redisclient.smembers('divisions')

        for divisionId in divisions:
            division = divisionId
            # division_name = redisclient.hgetasstring(division, 'name')
            leagues[division] = self.compile_league(division, segment_efforts)

        return leagues


    def compile_league(self, league_name, effort_list):
        members = redisclient.smembers(league_name + '_members')
        times = []
        efforts = {}

        # Compile dict of best efforts for each athlete in this league
        for effort in effort_list:
            athlete_id = effort['athlete']['id']

            if str(athlete_id) in members:
                if athlete_id in efforts:
                    if effort['elapsed_time'] >= efforts[athlete_id]['elapsed_time']:
                        continue

                efforts[athlete_id] = effort

        # Enrich with athlete details, and collect list of times for ranking
        for athlete_id, effort in efforts.items():
            athlete = Athlete(athlete_id).get()

            for k, v in athlete.items():
                effort['athlete'][k] = v

            corrected_time = effort['elapsed_time']

            neutralised_times = []
            for key, value in effort['neutralised'].items():
                corrected_time = corrected_time - value
                neutralised_times.append(str(value))

            effort['neutralised_times_formatted'] = ', '.join(neutralised_times)

            minutes = int(effort['elapsed_time'] / 60)
            seconds = effort['elapsed_time'] % 60
            effort['elapsed_time_formatted'] = "%d.%02d" % (minutes, seconds)

            minutes = corrected_time / 60
            seconds = corrected_time % 60
            effort['corrected_time'] = corrected_time
            effort['corrected_time_formatted'] = "%d.%02d" % (minutes, seconds)

            start_time_formatted = datetime.strptime(effort['start_date_local'], "%Y-%m-%dT%H:%M:%SZ")
            effort['start_time_formatted'] = start_time_formatted.strftime('%a %d/%m, %H:%M')

            times.append(corrected_time)

        times = list(set(times))
        times.sort()
        rank = 1

        # Assign a rank to each effort
        for time in times:
            joint = 0

            for athlete_id, effort in efforts.items():
                if effort['corrected_time'] == time:
                    effort['rank'] = rank
                    effort['points'] = max(11 - rank, 0)
                    joint = joint + 1

            rank = rank + max(joint, 1)

        s = OrderedDict(sorted(efforts.items(), key=lambda t: t[1]['rank']))

        return s