from urllib.request import urlopen
from urllib.parse import urlencode
from contextlib import closing
import urllib.request
import urllib
import json


def getfromurl(url):
  with urllib.request.urlopen(url, timeout=5) as response:
    ret = response.read().decode('utf-8')

  return ret

def getjsonfromurl(uri, parameters, token):
    authz = 'Bearer ' + token

    full_uri = uri + '?' + urllib.parse.urlencode(parameters)

    req = urllib.request.Request(full_uri)
    req.add_header('Authorization', authz)

    with closing(urlopen(req)) as response:
        data = json.loads(response.read().decode())
        return data
