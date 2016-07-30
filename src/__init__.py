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


from flask import Flask, request, render_template, session, redirect
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

app = Flask(__name__)
redisclient('localhost', 6379)
core = AlbaSotwCore()

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
    'redirect_uri':  'http://212.159.46.52:5000/callback',
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

    neutral_segments = []

    if neutral_segment_1_id != None: neutral_segments.append(neutral_segment_1_id)
    if neutral_segment_2_id != None: neutral_segments.append(neutral_segment_2_id)
    if neutral_segment_3_id != None: neutral_segments.append(neutral_segment_3_id)

    core.add_sotw(main_segment_id, neutral_zones=neutral_segments)

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

@app.route('/efforts')
def efforts():
    user_profile=None
    error=None

    if 'profile' in session:
        user_profile = session['profile']

    try:
        leagues=core.compile_efforts()
    except Exception as ex:
        leagues=None
        error=ex

    return render_template('efforts.html', leagues=leagues, user=user_profile, error=error)

@app.route('/getsegment/<segment_id>')
def get_segment(segment_id):
    segment_data = Segment(segment_id).get()
    return json.dumps(segment_data)

if __name__ == '__main__':
    app.secret_key = 'super secret key'
    app.config['SESSION_TYPE'] = 'filesystem'

    app.run(debug=True, host='0.0.0.0', threaded=True)


