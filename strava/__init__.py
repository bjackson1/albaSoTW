import webrequest
from storage import redisclient
from datetime import datetime

class Strava:
    API_URL = 'https://www.strava.com/api/v3'
    PAGE_SIZE = 200

    def get_efforts(self, segment, starttime , endtime):
        access_token = self.get_access_token()
        returned_results = -1
        effort_list = []
        page = 1

        while returned_results < 0 or returned_results == self.PAGE_SIZE:
            efforts = webrequest.getjsonfromurl(self.API_URL + '/segments/' + segment + '/all_efforts',
                                             {'start_date_local': starttime.isoformat(), #'2016-04-03T00.00.00',
                                              'end_date_local': endtime.isoformat(), #'2016-04-04T18.00.00',
                                              'per_page': str(self.PAGE_SIZE),
                                              'page': page},
                                             access_token)

            returned_results = len(efforts)
            effort_list = effort_list + efforts
            page = page + 1

        return effort_list

    def get_athlete(self, athlete_id):
        access_token = self.get_access_token()

        athlete_object = webrequest.getjsonfromurl('%s/athletes/%s' % (self.API_URL, athlete_id), token=access_token)

        return athlete_object

    def get_segment(self, segment_id):
        access_token = self.get_access_token()

        segment_object = webrequest.getjsonfromurl('%s/segments/%s' % (self.API_URL, segment_id), token=access_token)

        return segment_object

    def get_access_token(self):
        return redisclient.get('api_token')

