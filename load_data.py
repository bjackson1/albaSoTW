
import os
import yaml
from storage import redisclient
import json

class loader:
    def loadconfig(self, file):
        SCRIPTPATH = os.path.dirname(os.path.realpath(__file__))
        cfgstream = open(SCRIPTPATH + '/' + file)
        config = yaml.load(cfgstream)
        return config


    def setupTestData(self, file):
        redisclient('192.168.1.2', 6379)
        config = self.loadconfig(file)['redis']

        redisclient.set('api_token', config['api_token'])
        redisclient.set('sotw', config['sotw'])

        for member in config['members']:
            member_data = config['members'][member]

            for key, value in member_data.items():
                redisclient.hset(member, key, value)

        try:
            redisclient.delete('divisions')
        except Exception as e:
            print(e)

        for division in config['divisions']:
            division_data = config['divisions'][division]

            redisclient.sadd('divisions', division)
            redisclient.hset(division, 'name', division_data['name'])

            try:
                redisclient.delete(division + '_members')
            except Exception as e:
                print(e)

            for value in division_data['members']:
                redisclient.sadd(division + '_members', value)

        config['loaded_efforts'] = json.loads(config['efforts'])

        return config

