import sys

sys.path.append('/var/www/homeautomation/web')

import redis


class redisclient:
    redisconnection = None

    def __init__(self, address, port):
        redisclient.redisconnection = redis.StrictRedis(host=address, port=port, db=0)

    def get(key):
        return redisclient.redisconnection.get(key)

    def getasstring(key):
        return redisclient.get(key).decode('utf-8')

    def getasint(key):
        return int(redisclient.get(key).decode('utf-8'))

    def set(key, value):
        redisclient.redisconnection.set(key, value)