
from flask import Flask, request, render_template, session, redirect, current_app, g
from urllib.request import urlopen
from urllib.parse import urlencode
from contextlib import closing
import random
import json
from athlete import Athlete
from segment import Segment
from division import Division
from storage import redisclient
from segment_of_the_week import SegmentOfTheWeek
import os, requests
from functools import wraps
from collections import OrderedDict
from datetime import date, datetime, timedelta
import logging

app = Flask(__name__)

if 'REDIS_PORT' in os.environ:
    redis_addr = os.environ['REDIS_PORT']
else:
    redis_addr = 'tcp://localhost:6379'

redis_port = redis_addr.split(':')[2]
redis_ip = redis_addr.split('//')[1].split(':')[0]
redisclient(redis_ip, redis_port)

log = logging.getLogger('sotw.frontend')


@app.before_request
def log_request():
    g.transaction_id = random.randint(0, 100000)
    log.info('Method=BeforeRequest Transaction=%s URL=%s ClientIP=%s Method=%s Proto=%s UserAgent=%s'
             % (g.transaction_id,
                request.url,
                request.headers.environ['REMOTE_ADDR'],
                request.headers.environ['REQUEST_METHOD'],
                request.headers.environ['SERVER_PROTOCOL'],
                request.headers.environ['HTTP_USER_AGENT']))


def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        admin = session.get('profile', {}).get('user_metadata', {}).get('admin', {})

        if 'profile' not in session or (admin != 'true'):
            return redirect('/efforts')
        return f(*args, **kwargs)

    return decorated


@app.route('/')
def root_page():
    return redirect('/efforts')


@app.route('/setsotw/<main_segment_id>')
@app.route('/setsotw/<main_segment_id>/<neutral_segment_1_id>')
@app.route('/setsotw/<main_segment_id>/<neutral_segment_1_id>/<neutral_segment_2_id>')
@app.route('/setsotw/<main_segment_id>/<neutral_segment_1_id>/<neutral_segment_2_id>/<neutral_segment_3_id>')
@requires_auth
def set_sotw(main_segment_id, neutral_segment_1_id=None, neutral_segment_2_id=None, neutral_segment_3_id=None):
    log.info('Method=set_sotw Transaction=%s  MainSegment=%s NeutralSegment1=%s NeutralSegment2=%s NeutralSegment3=%s'
             % (g.transaction_id,
                main_segment_id,
                neutral_segment_1_id,
                neutral_segment_2_id,
                neutral_segment_3_id))
    neutral_segments = []

    if neutral_segment_1_id != None: neutral_segments.append(neutral_segment_1_id)
    if neutral_segment_2_id != None: neutral_segments.append(neutral_segment_2_id)
    if neutral_segment_3_id != None: neutral_segments.append(neutral_segment_3_id)

    try:
        sotw = SegmentOfTheWeek(main_segment_id=main_segment_id, neutral_zone_ids=neutral_segments)
        sotw.save()
        log.info('SotW successfully set')
    except Exception as e:
        log.exception('Failed to add SOTW')

    return "SoTW set to %s" % main_segment_id


@app.route('/admin')
@requires_auth
def add_athlete_page():
    divisions = Division.get_all()

    return render_template('admin.html', divisions=divisions)


@app.route('/removeathlete/<athlete_id>')
@requires_auth
def remove_athlete(athlete_id):
    Division.remove_athlete_from_all_divisions(athlete_id)

    return "OK"


@app.route('/addathlete/<athlete_id>/<division>')
@requires_auth
def add_athlete(athlete_id, division):
    if Division(division).add_athlete(athlete_id):
        athlete = Athlete(athlete_id)

        return json.dumps(athlete.__dict__)
    else:
        return 'Incorrect gender for Division'


@app.route('/updateefforts/<year>/<week_number>')
@app.route('/updateefforts')
def update_efforts(year=None, week_number=None):
    transaction_start_time = datetime.now()
    log.info('Method=update_efforts Transaction=%s Year=%s WeekNumber=%s' % (g.transaction_id, year, week_number))

    sotw = SegmentOfTheWeek(year=year, week_number=week_number)
    sotw.update_all_results()

    log.info('Method=update_efforts Message="Process complete"')

    time_taken = datetime.now() - transaction_start_time
    log.info('PERF Method=updateefforts ms=%s' % (time_taken.microseconds))
    return "OK"


@app.route('/efforts')
@app.route('/efforts/<year>/<week_number>')
def efforts(year=None, week_number=None):
    transaction_start_time = datetime.now()
    log.info('Method=efforts Transaction=%s Year=%s WeekNumber=%s' % (g.transaction_id, year, week_number))

    sotw_challenges = SegmentOfTheWeek.get_all_challenges_data()

    sotw = SegmentOfTheWeek(year=year, week_number=week_number)
    sotw.load_all_results()

    results_table = render_template('results_table.html', divisions=sotw.results)

    user_profile=None

    if 'profile' in session:
        user_profile = session['profile']

    log.debug('Method=efforts Message="Rendering page"')
    rendered_page = render_template('efforts.html', results_table=results_table, user=user_profile, this_week=[sotw.year, sotw.week_number], sotw_challenges=sotw_challenges)
    log.debug('Method=efforts Message="Page rendered" Length=%s DataSample="%s"' % (len(rendered_page), rendered_page[:10]))
    time_taken = datetime.now() - transaction_start_time
    log.info('PERF Method=efforts ms=%s' % (time_taken.microseconds))

    return rendered_page


@app.route('/getsegment/<segment_id>')
def get_segment(segment_id):
    segment_data = Segment(segment_id).get()
    return json.dumps(segment_data)







# Auth methods
@app.route('/logout')
def logout():
    session.pop('profile')
    return redirect('/efforts')


# Here we're using the /callback route.
@app.route('/callback')
def callback_handling():
  env = os.environ
  code = request.args.get('code')

  json_header = {'content-type': 'application/json'}

  token_url = "https://{domain}/oauth/token".format(domain='albasotw.auth0.com')

  token_payload = {
    'client_id':     'f9dF4rSZNvgJhiRe1EFJsg1ymJlmih2k',
    'client_secret': '8_Qh1mXIddjq49PANkJOEHhJC_4jA9ewsO4Y7IXhdFoSwg-bJgdYwDBsMb5JCQDD',
    'redirect_uri':  'http://az-bcj-01.cloudapp.net/callback',
    'code':          code,
    'grant_type':    'authorization_code'
  }

  token_info = requests.post(token_url, data=json.dumps(token_payload), headers = json_header).json()

  user_url = "https://{domain}/userinfo?access_token={access_token}" \
      .format(domain='albasotw.auth0.com', access_token=token_info['access_token'])

  user_info = requests.get(user_url).json()

  # We're saving all user information into the session
  session['profile'] = user_info

  # Redirect to the User logged in page that you want here
  # In our case it's /dashboard
  return redirect('/efforts')







