
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
from core import AlbaSotwCore
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
core = AlbaSotwCore()

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
    log.info('Method=update_efforts Transaction=%s Year=%s WeekNumber=%s' % (g.transaction_id, year, week_number))
    leagues={}

    try:
        if year != None and week_number != None:
            leagues=core.compile_efforts(year=year, week_number=week_number)
        else:
            leagues=core.compile_efforts()

        log.info('Leagues compiled Count=%s' % len(leagues))

    except Exception as ex:
        log.exception('Failed to compile leagues')
        leagues=None
        error=ex
        return "Failed"

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
    log.info('Method=efforts Transaction=%s Year=%s WeekNumber=%s' % (g.transaction_id, year, week_number))
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
            sorted_results[division] = {}
            sorted_results[division]['name'] = table['name']
            sorted_results[division]['results'] = OrderedDict(sorted(table['results'].items(), key=lambda t: t[1]['rank']))
    else:
        log.info('Method=efforts Message="No data found for selected period"')

    log.debug('Method=efforts Message="Getting result sets list from redis"')
    result_sets = []
    result_keys = redisclient.keys("results_*")
    log.debug('Method=efforts Message="Results keys retrieved" ResultKeys="%s"' % result_keys)

    for result_key in result_keys:
        result_year = result_key.split('_')[1]
        result_week_number = result_key.split('_')[2]
        week_commencing = date(year=int(result_year), month=1, day=4) + timedelta(days=(int(result_week_number) - 1) * 7)
        segment_id = redisclient.get('sotw_%s_%s_segment' % (result_year, result_week_number))
        result = {'year': result_year,
                  'week': result_week_number,
                  'order_key': '%s.%s' % (result_year, result_week_number),
                  'week_commencing': week_commencing}

        if segment_id:
            segment = Segment(segment_id)
            result['segment'] = segment.get()

        result_sets.append(result)



    from operator import itemgetter
    sorted_result_sets = sorted(result_sets, key=itemgetter('order_key'), reverse=True)

    log.debug('Method=efforts Message="Rendering page"')
    rendered_page = render_template('efforts.html', leagues=sorted_results, user=user_profile, error=error, result_sets=sorted_result_sets, this_week=[year, week_number])
    log.debug('Method=efforts Message="Page rendered" Length=%s DataSample="%s"' % (len(rendered_page), rendered_page[:10]))
    time_taken = datetime.now() - transaction_start_time
    log.info('PERF Method=efforts ms=%s' % (time_taken.microseconds))

    return rendered_page


@app.route('/getsegment/<segment_id>')
def get_segment(segment_id):
    segment_data = Segment(segment_id).get()
    return json.dumps(segment_data)



