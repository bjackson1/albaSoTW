import webrequest
from storage import redisclient
from datetime import datetime

class Strava:
    API_URL = 'https://www.strava.com/api/v3'
    PAGE_SIZE = 50


    def get_efforts(self, segment, start_datetime, end_datetime):
        access_token = self.get_access_token()
        returned_results = -1
        effort_list = []
        page = 1

        while returned_results < 0 or returned_results == self.PAGE_SIZE:
            try:
                efforts = webrequest.getjsonfromurl(self.API_URL + '/segments/' + str(segment) + '/all_efforts',
                                                 {'start_date_local': start_datetime.isoformat(), #'2016-04-03T00.00.00',
                                                  'end_date_local': end_datetime.isoformat(), #'2016-04-04T18.00.00',
                                                  'per_page': str(self.PAGE_SIZE),
                                                  'page': page},
                                                 access_token)

                returned_results = len(efforts)
                effort_list = effort_list + efforts
                page = page + 1
            except Exception as e:
                print(e)
                raise(e)

        return effort_list


    # Implemented to support mocking, allowing neutral efforts to return a different result set,
    #   until I can find a better way of doing this...
    def get_neutralised_efforts(self, segment, start_datetime, end_datetime):
        return self.get_efforts(segment, start_datetime, end_datetime)


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

