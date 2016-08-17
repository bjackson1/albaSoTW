from datetime import date, timedelta, datetime
import logging, inspect, functools
from storage import redisclient
from strava import Strava

log = logging.getLogger('sotw.sotw')


class SegmentOfTheWeek:
    def __init__(self, year=None, week_number=None, main_segment_id=None, neutral_zone_ids=None):
        log.debug("Method=init Year=%s WeekNumber=%s MainSegmentId=%s NeutralZoneIds=%s" % (year, week_number, main_segment_id, neutral_zone_ids))

        self.year, self.week_number, self.main_segment_id, self.neutral_zone_ids = self.validate_and_clean(year, week_number, main_segment_id, neutral_zone_ids)
        self.year, self.week_number = self.get_period(self.year, self.week_number)

        self.start_datetime, self.end_datetime = self.get_start_end_datetimes()
        self.key_name = self.get_key_name()

        if main_segment_id == None:
            self.main_segment_id, self.neutral_zone_ids = self.get_segment_ids()
        else:
            self.main_segment_id = main_segment_id
            self.neutral_zone_ids = []

            if neutral_zone_ids != None:
                self.neutral_zone_ids = neutral_zone_ids

        log.debug(
            "Method=init Message='Initialised with values' Year=%s WeekNumber=%s MainSegmentId=%s NeutralZoneIds=%s StartDateTime=%s EndDateTime=%s KeyName=%s" %
                (self.year, self.week_number, self.main_segment_id, self.neutral_zone_ids, self.start_datetime, self.end_datetime, self.key_name))


    def get_period(self, year=None, week_number=None):
        today = date.today()

        if year == None:
            year = today.year

        if week_number == None:
            week_number = today.isocalendar()[1]

        return year, week_number


    def get_start_end_datetimes(self):
        start_date = datetime.strptime("%s-W%s-0" % (self.year, self.week_number), "%Y-W%W-%w")
        start_datetime = datetime.combine(start_date - timedelta(start_date.weekday()), datetime.min.time())
        log.debug('Method=get_start_end_datetimes StartDateTime=%s', start_datetime)

        end_datetime = start_datetime + timedelta(days=6, hours=20)
        log.debug('Method=get_start_end_datetimes EndDateTime=%s', end_datetime)

        return start_datetime, end_datetime


    def get_key_name(self):
        return 'sotw_%s_%02d' % (self.year, self.week_number)


    def get_segment_ids(self):
        main_segment_id = redisclient.get('%s_segment' % self.key_name)
        log.debug('Method=get_segment_ids Segment=%s' % main_segment_id)

        neutral_zone_ids = redisclient.smembers('%s_neutral_zones' % self.key_name)
        log.debug('Method=get_segment_ids NeutralZones=%s' % neutral_zone_ids)

        y, w, main_segment_id, neutral_zone_ids = self.validate_and_clean(main_segment_id=main_segment_id, neutral_zone_ids=neutral_zone_ids)

        log.info('Method=get_segment_ids Message="Got data from Redis" MainSegmentId=%s NeutralZonesIds=%s' % (main_segment_id, neutral_zone_ids))
        return main_segment_id, neutral_zone_ids


    def save(self):
        log.info('Method=%s, SegmentId=%s, NeutralZones=%s' % ('save', self.main_segment_id, self.neutral_zone_ids))
        redisclient.set('%s_segment' % self.key_name, self.main_segment_id)

        if self.neutral_zone_ids != []:
            for neutral_zone_id in self.neutral_zone_ids:
                redisclient.sadd('%s_neutral_zones' % self.key_name, neutral_zone_id)


    def validate_and_clean(self, year=None, week_number=None, main_segment_id=None, neutral_zone_ids=None):
        if year != None:
            if (type(year) is str and year.isdigit()) or type(year) is int:
                year = int(year)
                if year < 2000 or year > 2999:
                    raise(Exception)
            else:
                raise(Exception)

        if week_number != None:
            if (type(week_number) is str and week_number.isdigit()) or type(week_number) is int:
                week_number = int(week_number)
                if week_number < 1 or week_number > 52:
                    raise(Exception)
            else:
                raise(Exception)

        if main_segment_id != None:
            if (type(main_segment_id) is str and main_segment_id.isdigit()) or type(main_segment_id) is int:
                main_segment_id = int(main_segment_id)
            else:
                raise(Exception)

        new_neutral_zone_ids = set()
        if neutral_zone_ids != None:
            if type(neutral_zone_ids) is set:
                for segment_id in neutral_zone_ids:
                    if (type(segment_id) is str and segment_id.isdigit()) or type(segment_id) is int:
                        cast_segment_id = int(segment_id)
                        new_neutral_zone_ids.add(cast_segment_id)
                    else:
                        raise(Exception)
            else:
                raise(Exception)

        return year, week_number, main_segment_id, new_neutral_zone_ids


    def update_efforts(self):
        if self.main_segment_id != None:
            self.segment_efforts = {}

            log.info(
                'Method=load_efforts Message="Getting main segment data from Strava" Segment=%s StartTime=%s EndTime=%s'
                % (self.main_segment_id, self.start_datetime, self.end_datetime))

            try:
                segment_efforts = Strava().get_efforts(self.main_segment_id, self.start_datetime, self.end_datetime)
                log.info('Method=load_efforts Message="Data from Strava" ResultCount=%s' % (len(segment_efforts)))

                for segment_effort in segment_efforts:
                    self.segment_efforts[segment_effort['activity']['id']] = segment_effort
                    self.segment_efforts[segment_effort['activity']['id']]['neutral_efforts'] = []

            except Exception as e:
                log.exception('Method=load_efforts Message="Strava call failed"')
                raise(e)

            if self.neutral_zone_ids != None:
                for neutral_segment_id in self.neutral_zone_ids:
                    log.info(
                        'Method=load_efforts Message="Getting main segment data from Strava" Segment=%s StartTime=%s EndTime=%s'
                        % (neutral_segment_id, self.start_datetime, self.end_datetime))

                    try:
                        segment_efforts = Strava().get_efforts(neutral_segment_id, self.start_datetime, self.end_datetime)
                        log.info(
                            'Method=load_efforts Message="Data from Strava" ResultCount=%s' % (len(segment_efforts)))

                        for segment_effort in segment_efforts:
                            if segment_effort['activity']['id'] in self.segment_efforts:
                                self.segment_efforts[segment_effort['activity']['id']]['neutral_efforts'].append(segment_effort)

                    except Exception as e:
                        log.exception('Method=load_efforts Message="Strava call failed"')
                        raise (e)

    def enrich_efforts(self):
        if self.segment_efforts != None:
            for segment_effort_id, segment_effort in self.segment_efforts.items():

                # Calculate Neutralised Times
                neutralised_times = []
                for neutral_zone_effort in segment_effort['neutral_efforts']:
                    neutralised_times.append(neutral_zone_effort['elapsed_time'])

                segment_effort['neutralised_times'] = neutralised_times

                # Calculate Net Effort Time
                segment_effort['net_elapsed_time'] = segment_effort['elapsed_time'] - sum(neutralised_times)

                segment_effort['pace_kph'] = round((segment_effort['distance']/1000) / (segment_effort['net_elapsed_time']/60/60), 2)
                segment_effort['pace_mph'] = round(segment_effort['pace_kph'] / 1.61, 2)

    # def compile_efforts(self, year=None, week_number=None):
    #     log.info('Method=compile_efforts Year=%s WeekNumber=%s' % (year, week_number))
    #     leagues = {}
    #
    #     starttime = datetime.combine(date.today() - timedelta(date.today().weekday()), datetime.min.time())
    #     key_name = self.get_sotw_key_name()
    #
    #     if year != None and week_number != None:
    #         key_name = 'sotw_%s_%s' % (year, week_number)
    #         d = "%s-W%s" % (year, week_number)
    #         r = datetime.strptime(d + '-0', "%Y-W%W-%w")
    #         starttime = datetime.combine(r - timedelta(r.weekday()), datetime.min.time())
    #
    #     endtime = starttime + timedelta(days=6, hours=20)
    #     log.info('Method=compile_efforts ResultKey=%s' % key_name)
    #
    #     log.info('Method=compile_efforts Message="Getting segment data from redis"')
    #
    #     segment = redisclient.get('%s_segment' % key_name)
    #     log.info('Method=compile_efforts Segment=%s' % segment)
    #
    #     neutral_zones = redisclient.smembers('%s_neutral_zones' % key_name)
    #     log.info('Method=compile_efforts NeutralZones=%s' % neutral_zones)
    #
    #     if segment != None:
    #         log.info(
    #             'Method=compile_efforts Message="Getting main segment data from Strava" Segment=%s StartTime=%s EndTime=%s'
    #             % (segment, starttime, endtime))
    #         try:
    #             segment_efforts = Strava().get_efforts(segment, starttime, endtime)
    #             log.info('Method=compile_efforts Message="Data from Strava" ResultCount=%s' % (len(segment_efforts)))
    #         except Exception as e:
    #             log.exception('Method=compile_efforts Message="Strava call failed"')
    #             raise(e)
    #
    #         for segment_effort in segment_efforts:
    #             segment_effort['neutralised'] = {}
    #
    #         for neutral_zone in neutral_zones:
    #             log.info(
    #                 'Method=compile_efforts Message="Getting neutral zone segment data from Strava" Segment=%s StartTime=%s EndTime=%s'
    #                 % (neutral_zone, starttime, endtime))
    #
    #             try:
    #                 neutral_zone_efforts = Strava().get_efforts(neutral_zone, starttime, endtime)
    #                 log.info('Method=compile_efforts Message="Data from Strava" ResultCount=%s' % (len(neutral_zone_efforts)))
    #             except Exception as e:
    #                 log.exception('Method=compile_efforts Message="Strava call failed"')
    #                 raise (e)
    #
    #             for neutral_zone_effort in neutral_zone_efforts:
    #                 for segment_effort in segment_efforts:
    #                     if neutral_zone_effort['activity']['id'] == segment_effort['activity']['id']:
    #                         segment_effort['neutralised'][neutral_zone] = neutral_zone_effort['elapsed_time']
    #
    #         divisions = redisclient.smembers('divisions')
    #
    #         for divisionId in divisions:
    #             leagues[divisionId] = {}
    #             leagues[divisionId]['results'] = self.compile_league(divisionId, segment_efforts)
    #             leagues[divisionId]['name'] = redisclient.hget(divisionId, 'name')
    #
    #     else:
    #         log.info('Method=compile_efforts Message="No SotW configured for the period" ResultSet=%s' % (key_name))
    #
    #     return leagues

    # def compile_league(self, league_name, effort_list):
    #     log.debug('Method=compile_league LeagueName=%s EffortListLength=%s' % (league_name, len(effort_list)))
    #
    #     members = redisclient.smembers(league_name + '_members')
    #     log.debug('Method=compile_league LeagueMembers=%s' % members)
    #     times = []
    #     efforts = {}
    #
    #     # Compile dict of best efforts for each athlete in this league
    #     for effort in effort_list:
    #         athlete_id = effort['athlete']['id']
    #         # log.debug('Method=compile_league Message="Finding effort for athlete" AthleteId=%s' % (athlete_id))
    #
    #         if str(athlete_id) in members:
    #             if athlete_id in efforts:
    #                 if effort['elapsed_time'] >= efforts[athlete_id]['elapsed_time']:
    #                     continue
    #
    #             log.debug('Method=compile_league Message="Attributing effort to athlete" AthleteId=%s EffortId=%s' % (athlete_id, effort['id']))
    #             efforts[athlete_id] = effort
    #
    #     # Enrich with athlete details, and collect list of times for ranking
    #     for athlete_id, effort in efforts.items():
    #         athlete = Athlete(athlete_id).get()
    #
    #         for k, v in athlete.items():
    #             effort['athlete'][k] = v
    #
    #         corrected_time = effort['elapsed_time']
    #
    #         neutralised_times = []
    #         for key, value in effort['neutralised'].items():
    #             corrected_time = corrected_time - value
    #             neutralised_times.append(str(value))
    #
    #         effort['neutralised_times_formatted'] = ', '.join(neutralised_times)
    #
    #         minutes = int(effort['elapsed_time'] / 60)
    #         seconds = effort['elapsed_time'] % 60
    #         effort['elapsed_time_formatted'] = "%d:%02d" % (minutes, seconds)
    #
    #         minutes = corrected_time / 60
    #         seconds = corrected_time % 60
    #         effort['corrected_time'] = corrected_time
    #         effort['corrected_time_formatted'] = "%d:%02d" % (minutes, seconds)
    #
    #         effort['pace_kph'] = round((effort['distance']/1000) / (effort['corrected_time']/60/60), 2)
    #         effort['pace_mph'] = round((effort['distance']/1000) / (effort['corrected_time']/60/60) / 1.61, 2)
    #
    #         if 'average_heartrate' in effort:
    #             effort['average_heartrate_formatted'] = int(effort['average_heartrate'])
    #
    #         if 'average_watts' in effort:
    #             effort['average_watts_formatted'] = int(effort['average_watts'])
    #
    #         start_time_formatted = datetime.strptime(effort['start_date_local'], "%Y-%m-%dT%H:%M:%SZ")
    #         effort['start_time_formatted'] = start_time_formatted.strftime('%a %d/%m, %H:%M')
    #
    #         log.debug(
    #             'Method=compile_league Message="Recording elapsed time" AthleteId=%s EffortId=%s NeutralisedTimes="%s" ElapsedTime=%s CorrectedTime=%s StartTime="%s"'
    #             % (athlete_id,
    #                effort['id'],
    #                effort['neutralised_times_formatted'],
    #                effort['elapsed_time_formatted'],
    #                effort['corrected_time_formatted'],
    #                effort['start_time_formatted']))
    #
    #         times.append(corrected_time)
    #
    #     times = list(set(times))
    #     times.sort()
    #     rank = 1
    #
    #     # Assign a rank to each effort
    #     for time in times:
    #         joint = 0
    #
    #         for athlete_id, effort in efforts.items():
    #             if effort['corrected_time'] == time:
    #                 effort['rank'] = rank
    #                 effort['points'] = max(11 - rank, 0)
    #                 joint = joint + 1
    #
    #                 log.debug('Method=compile_league Message="Ranking athlete/effort" AthleteId=%s EffortId=%s Rank=%s Points=%s'
    #                     % (athlete_id,
    #                        effort['id'],
    #                        effort['rank'],
    #                        effort['points']))
    #
    #         rank = rank + max(joint, 1)
    #
    #     log.debug('Method=compile_league Message="Completed compilation"' % ())
    #     return efforts
    #
