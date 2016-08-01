#!/usr/bin/env python

# Each week a segment is manually voted for on Facebook.
# Segments that go through red lights may have one or two refunds, where times from a seperate segment is taken off the final time
# League tables get updated after the close off period/during the week
#  ... and results get auto-posted to Facebook.
# Leagues run for 1 quarter, and then 4 riders per division get relegated/promoted (apart from ladies as they have one division)
# If a rider doesn't post a time at all during a quarter then they are also relegated and more riders promoted from the division below.
# Solution needs to post/update the league tables and weekly results onto the current Wordpress albarosacc.com website.
# Needs to be able to still do manual entries/adjustments for complicated segments or multi segment weeks.
#
#
# Known issues
#
# 1. If a segment spans a month then Strava fails to show all times if the view is selected by "this week"

# Priorities
#  - Neutral Zones
#  - Admin auth


from flask import Flask, request, render_template, session, redirect, current_app
from urllib.request import urlopen
from urllib.parse import urlencode
from contextlib import closing
import random
import json
from athlete import Athlete
from segment import Segment
from division import Division
from storage import redisclient
from core import AlbaSotwCore
import os, requests
from functools import wraps
from collections import OrderedDict
from datetime import date, datetime, timedelta
import logging

app = Flask(__name__)
redisclient('localhost', 6379)
core = AlbaSotwCore()

log = logging.getLogger('sotw.frontend')

@app.before_request
def log_request():
    log.info('URL=%s ClientIP=%s Method=%s Proto=%s UserAgent=%s'
             % (request.url,
                request.headers.environ['REMOTE_ADDR'],
                request.headers.environ['REQUEST_METHOD'],
                request.headers.environ['SERVER_PROTOCOL'],
                request.headers.environ['HTTP_USER_AGENT']))
    # transaction = random.randint(0, 100000)
    # request.['transaction'] = str(transaction)

@app.route('/connect')
def connect():
    state = random.randint(0, 2000000000)

    return render_template("connect.html", state=state)

@app.route('/exchange')
def token_exchange():
    code = request.args.get('code')

    client_id=redisclient.hget('api', 'client_id')
    client_secret=redisclient.hget('api', 'client_token')

    exch_uri = 'https://www.strava.com/oauth/token'
    data = urlencode({'client_id' : client_id, 'client_secret' : client_secret, 'code' : code}).encode()

    with closing(urlopen(exch_uri, data)) as response:
        user_profile=json.loads(response.read().decode())

        athlete = Athlete(user_profile['athlete']['id']).get()

        return render_template('connected.html', athlete=athlete)

@app.route('/logout')
def logout():
    session.pop('profile')
    return redirect('/efforts')

@app.route('/')
def root_page():
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

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        admin = session.get('profile', {}).get('user_metadata', {}).get('admin', {})

        if 'profile' not in session or (admin != 'true'):
            return redirect('/efforts')
        return f(*args, **kwargs)

    return decorated

@app.route('/setsotw/<main_segment_id>')
@app.route('/setsotw/<main_segment_id>/<neutral_segment_1_id>')
@app.route('/setsotw/<main_segment_id>/<neutral_segment_1_id>/<neutral_segment_2_id>')
@app.route('/setsotw/<main_segment_id>/<neutral_segment_1_id>/<neutral_segment_2_id>/<neutral_segment_3_id>')
@requires_auth
def set_sotw(main_segment_id, neutral_segment_1_id=None, neutral_segment_2_id=None, neutral_segment_3_id=None):
    log.info('set_sotw MainSegment=%s NeutralSegment1=%s NeutralSegment2=%s NeutralSegment3=%s'
             % (main_segment_id,
                neutral_segment_1_id,
                neutral_segment_2_id,
                neutral_segment_3_id))
    neutral_segments = []

    if neutral_segment_1_id != None: neutral_segments.append(neutral_segment_1_id)
    if neutral_segment_2_id != None: neutral_segments.append(neutral_segment_2_id)
    if neutral_segment_3_id != None: neutral_segments.append(neutral_segment_3_id)

    try:
        core.add_sotw(main_segment_id, neutral_zones=neutral_segments)
        log.info('SotW successfully set')
    except Exception as e:
        log.exception('Failed to add SOTW')

    return "SoTW set to %s" % main_segment_id

@app.route('/admin')
@requires_auth
def add_athlete_page():
    divisions = Division.get_all(True)

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

        return json.dumps(athlete.get())
    else:
        return 'Incorrect gender for Division'

@app.route('/loaddata/<dataset>')
@requires_auth
def load_data(dataset):
    from load_data import loader

    loader().setupTestData('%s_data.yml' % dataset)

    return "OK"

def get_results_key(year=None, week_number=None):

    if year == None or week_number == None:
        week_number = date.today().isocalendar()[1]
        year = date.today().year

    return 'results_%s_%s' % (year, week_number)

@app.route('/updateefforts/<year>/<week_number>')
@app.route('/updateefforts')
def update_efforts(year=None, week_number=None):
    transaction_start_time = datetime.now()
    log.info('Method=update_efforts Year=%s WeekNumber=%s' % (year, week_number))

    try:
        if year != None and week_number != None:
            leagues = core.compile_efforts(year=year, week_number=week_number)
        else:
            leagues=core.compile_efforts()

        log.info('Leagues compiled Count=%s' % len(leagues))

    except Exception as ex:
        log.exception('Failed to compile leagues')
        leagues=None
        error=ex

    data = json.dumps(leagues)

    result_key=get_results_key(year=year, week_number=week_number)
    log.info('Method=update_efforts Message="Storing results" ResultKey=%s' % result_key)
    redisclient.set(result_key, data)

    log.info('Method=update_efforts Message="Process complete"')

    time_taken = datetime.now() - transaction_start_time
    log.info('PERF Method=updateefforts ms=%s' % (time_taken.microseconds))
    return "OK"

@app.route('/efforts')
@app.route('/efforts/<year>/<week_number>')
def efforts(year=None, week_number=None):
    transaction_start_time = datetime.now()
    log.info('Method=efforts Year=%s WeekNumber=%s' % (year, week_number))
    user_profile=None
    error=None
    sorted_results = None


    if year == None or week_number == None:
        result_set=get_results_key()
    else:
        result_set='results_%s_%s' % (year, week_number)

    if 'profile' in session:
        user_profile = session['profile']

    log.debug('Method=efforts Message="Getting data from redis" ResultSet=%s' % result_set)
    results_json = redisclient.get(result_set)
    log.debug('Method=efforts Message="Retrieved data from redis" Length=%s DataSample="%s"' % (len(results_json), results_json[:20]))

    if results_json != None and results_json != 'null':
        results = json.loads(results_json)
        log.debug('Method=efforts Message="Data parsed" ElementCount=%s' % len(results))

        sorted_results = {}

        log.debug('Method=efforts Message="Sorting Results"')
        for division, table in results.items():
            sorted_results[division] = OrderedDict(sorted(table.items(), key=lambda t: t[1]['rank']))
    else:
        log.info('Method=efforts Message="No data found for selected period"')


    log.debug('Method=efforts Message="Getting result sets list from redis"')
    result_sets = []
    result_keys = redisclient.keys("results_*")
    log.debug('Method=efforts Message="Results keys retrieved" ResultKeys="%s"' % result_keys)

    for result_key in result_keys:
        result_year = result_key.split('_')[1]
        result_week_number = result_key.split('_')[2]
        result_sets.append([result_year, result_week_number])

    log.debug('Method=efforts Message="Rendering page"')
    rendered_page = render_template('efforts.html', leagues=sorted_results, user=user_profile, error=error, result_sets=result_sets, this_week=[year, week_number])
    log.debug('Method=efforts Message="Page rendered" Length=%s DataSample="%s"' % (len(rendered_page), rendered_page[:10]))
    time_taken = datetime.now() - transaction_start_time
    log.info('PERF Method=efforts ms=%s' % (time_taken.microseconds))
    return rendered_page

@app.route('/getsegment/<segment_id>')
def get_segment(segment_id):
    segment_data = Segment(segment_id).get()
    return json.dumps(segment_data)



