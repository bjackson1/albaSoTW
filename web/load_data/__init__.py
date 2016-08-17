
import os
import yaml
from storage import redisclient
import json
from datetime import date


class loader:
    def loadconfig(self, file):
        SCRIPTPATH = os.path.dirname(os.path.realpath(__file__))
        with open(SCRIPTPATH + '/' + file) as cfgstream:
            config = yaml.load(cfgstream)
            return config


    def setupTestData(self, file):
        config = self.loadconfig(file)['redis']

        sotw_key = 'sotw_%s_%s' % (date.today().year, date.today().isocalendar()[1])

        redisclient.set('api_token', config['api_token'])
        redisclient.set('%s_segment' % sotw_key, config['sotw_current']['segment'])

        for neutral_zone in config['sotw_current']['neutral_zones']:
            redisclient.sadd('%s_neutral_zones' % sotw_key, neutral_zone)

        if 'members' in config:
            for member in config['members']:
                member_data = config['members'][member]

                for key, value in member_data.items():
                    redisclient.hset(member, key, value)

        # if 'segments' in config:
        #     for segment in config['segments']:
        #         segment_data = config['segments'][segment]

        try:
            redisclient.delete('divisions')
        except Exception as e:
            print(e)

        for division in config['divisions']:
            division_data = config['divisions'][division]

            redisclient.sadd('divisions', division)
            redisclient.hset(division, 'name', division_data['name'])
            redisclient.hset(division, 'sex', division_data['sex'])

            try:
                redisclient.delete(division + '_members')
            except Exception as e:
                print(e)

            if 'members' in division_data:
                for value in division_data['members']:
                    redisclient.sadd(division + '_members', value)

        if config['efforts']['segment']:
            config['loaded_efforts'] = json.loads(config['efforts']['segment'])

            if config['efforts']['neutral_zones']:
                config['loaded_neutral_zones'] = []
                for neutral_zone in config['efforts']['neutral_zones']:
                    loaded_neutral_zone_efforts = {}

                    for neutral_zone_effort in neutral_zone:
                        loaded_neutral_zone_efforts[neutral_zone_effort['id']] = neutral_zone_effort

                    config['loaded_neutral_zones'].append(loaded_neutral_zone_efforts)

        return config

