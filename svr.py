#!/usr/bin/env python

from flask import Flask
from flask import request
from flask import render_template
from socket import gethostname
from threading import Thread
from urllib.request import urlopen
from urllib.parse import urlencode
from contextlib import closing

import yaml
import urllib
import socket
import fcntl
import struct
import os
import time
import random
import json

from storage import redisclient

SCRIPTPATH=os.path.dirname(os.path.realpath(__file__))
MOBILETMPL="main.mobile.html"
#redisCli=redisClient('localhost', 6379)


app = Flask(__name__)

@app.route('/connect')
def connect():
  state = random.randint(0, 2000000000)

  return render_template("connect.html", state=state)

@app.route('/exchange')
def token_exchange():
  state = request.args.get('state')
  code = request.args.get('code')


  client_id=redisclient.get('client_id')
  client_secret=redisclient.get('client_secret')

  exch_uri = 'https://www.strava.com/oauth/token'
  data = urlencode({'client_id' : client_id, 'client_secret' : client_secret, 'code' : code}).encode()

  with closing(urlopen(exch_uri, data)) as response:
    #print(response.read().decode())
    user_profile=json.loads(response.read().decode())

    athlete = user_profile['athlete']['id']
    access_token = user_profile['access_token']

    redisclient.set(athlete, access_token)

    return render_template('connected.html', name=user_profile['athlete']['firstname'])

  return 'Failed'

if __name__ == '__main__':
#  createswitchworkers()
  redisclient('localhost', 6379)
  app.run(debug=True, host='0.0.0.0', threaded=True)

