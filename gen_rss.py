#!/usr/bin/env python3

import config

import requests
import pytz, datetime

import pprint

print("Hello. API_KEY={}".format(config.API_KEY))

target_timezone = pytz.timezone(config.TIMEZONE)
time_now = datetime.datetime.now(tz=target_timezone)

# Format looks like: 2017-03-25T00:00:00-0500
time_now_formatted = time_now.strftime("%Y-%m-%dT%H:%M:%S%z")

api_url='https://www.googleapis.com/calendar/v3/calendars/{}/events'.format(config.CALENDAR_ID_FULL)

api_params = { 
    'maxResults' : config.NUM_ITEMS,
    'orderBy' : 'startTime',
    'singleEvents' : 'true',
    'key' : config.API_KEY,
    'timeMin' : time_now_formatted,
    } 

r = requests.get(api_url, params=api_params)

# pprint.pprint(r)
# print("{}".format(r.url))
pprint.pprint(r.json())
