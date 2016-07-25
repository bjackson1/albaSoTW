#!/usr/bin/env python


# Each week a segment is manually voted for on Facebook.
# That segment then runs from Monday until 8pm Sunday.
# There are currently 4 mens divisions and 1 ladies.
# Points are awarded to the fastest 10 riders per division.
# Segments that go through red lights may have one or two refunds, where times from a seperate segment is taken off the final time
# League tables get updated after the close off period/during the week and results get auto-posted to Facebook.
# Leagues run for 1 quarter, and then 4 riders per division get relegated/promoted (apart from ladies as they have one division)
# If a rider doesn't post a time at all during a quarter then they are also relegated and more riders promoted from the division below.
# Solution needs to post/update the league tables and weekly results onto the current Wordpress albarosacc.com website.
# Needs to be able to still do manual entries/adjustments for complicated segments or multi segment weeks.
# Perhaps start off with manually running a task/pressing a button to check.
#
#
# Known issues
#
# 1. If a segment spans a month then Strava fails to show all times if the view is selected by "this week"

from flask import Flask
from flask import request
from flask import render_template
from urllib.request import urlopen
from urllib.parse import urlencode
from contextlib import closing
from datetime import datetime, timedelta, date
from strava import Strava

import yaml
import os
import random
import json
from collections import OrderedDict
from athlete import Athlete
from division import Division

from storage import redisclient

SCRIPTPATH=os.path.dirname(os.path.realpath(__file__))
MOBILETMPL="main.mobile.html"

app = Flask(__name__)

def loadconfig():
    cfgstream = open(SCRIPTPATH + '/config.yml')
    config = yaml.load(cfgstream)
    return config


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


@app.route('/setsotw')
def setsotwpage():
    return render_template('setsotw.html')

@app.route('/setsotw/<sotw>')
def setsotw(sotw):
    redisclient.set('sotw', sotw)
    return "SoTW set to %s" % sotw

@app.route('/addathlete')
def addathletepage():
    divisions = Division.get_all()

    return render_template('addathlete.html', divisions=divisions)

@app.route('/addathlete/<athlete_id>/<division>')
def addathlete(athlete_id, division):
    Division(division).add_athlete(athlete_id)

    return "Athlete %s added to division %s" % (athlete_id)


@app.route('/loadintdata')
def loadintdata():
    from load_data import loader

    loader().setupTestData('integration_data.yml')

    return "OK"


@app.route('/efforts')
def efforts():
    leagues=compile_efforts()

    return render_template('mytimes.html', leagues=leagues)


def compile_efforts():
    # access_token = redisclient.getasstring('api_token')
    segment = redisclient.getasstring('sotw')

    leagues = {}

    today = date.today()
    starttime = datetime.combine(today - timedelta(today.weekday()), datetime.min.time())
    endtime = starttime + timedelta(days=5, hours=20)

    effort_list = Strava().get_efforts(segment, starttime, endtime)

    divisions = redisclient.getlist('divisions')

    for divisionId in divisions:
        division = divisionId
        # division_name = redisclient.hgetasstring(division, 'name')
        leagues[division] = compile_league(division, effort_list)

    return leagues


def compile_league(league_name, effort_list):
    members = redisclient.getlist(league_name + '_members')
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

        minutes = int(effort['elapsed_time'] / 60)
        seconds = effort['elapsed_time'] % 60
        effort['elapsed_time_formatted'] = "%d.%02d" % (minutes, seconds)

        start_time_formatted = datetime.strptime(effort['start_date_local'], "%Y-%m-%dT%H:%M:%SZ")
        effort['start_time_formatted'] = start_time_formatted.strftime('%H:%M, %A %d/%m/%Y ')

        times.append(effort['elapsed_time'])

    times = list(set(times))
    times.sort()
    rank = 1

    # Assign a rank to each effort
    for time in times:
        joint = 0

        for athlete_id, effort in efforts.items():
            if effort['elapsed_time'] == time:
                effort['rank'] = rank
                effort['points'] = max(11 - rank, 0)
                joint = joint + 1

        rank = rank + max(joint, 1)

    s = OrderedDict(sorted(efforts.items(), key=lambda t: t[1]['rank']))

    return s


def init():
    redisclient('localhost', 6379)
    config = loadconfig()
    print("Config loaded")


if __name__ == '__main__':
    init()
    print("About to run")
    app.run(debug=True, host='0.0.0.0', threaded=True)

