#!/usr/bin/env python3

import config

import requests
import pytz, datetime, dateutil.parser
import jinja2

import pprint


TEMPLATE="/home/pnijjar/watcamp/python_rss/rss_template.jinja2"



def get_rfc822_datestring (google_date): 
    """ Convert whatever date Google is using to the RFC-822 dates
        that RSS wants.
    """

    # This is actually wrong because it ignores timezone.
    # See: http://stackoverflow.com/questions/19472859
    d = dateutil.parser.parse(google_date)

    """
    d = datetime.datetime.strptime(
        google_date,
        "%Y-%m-%dT%H:%M:%S.%fZ"
        )

    # Explicitly make the timezone UTC
    d.replace(tzinfo=pytz.utc)
    """

    # Output the proper format
    return d.strftime("%a, %d %b %y %T %z")



# --- Intro nonsense
print("Hello. API_KEY={}".format(config.API_KEY))

# --- Make API call 
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

cal_dict = r.json()


# --- Process template 

# This is kind of sketchy in general
feed_title = cal_dict['summary']


template_loader = jinja2.FileSystemLoader( searchpath="/" )
template_env = jinja2.Environment( loader=template_loader )
template_env.filters['rfc822'] = get_rfc822_datestring

template = template_env.get_template( TEMPLATE ) 
template_vars = { 
  "feed_title": feed_title,
  "feed_description": cal_dict['description'],
  "feed_builddate" : time_now.strftime("%a, %d %b %y %T %z"),
  "feed_pubdate" : cal_dict['updated'],
  "feed_website" : config.WEBSITE,
  }

output_rss = template.render(template_vars)


# pprint.pprint(r)
# print("{}".format(r.url))
# pprint.pprint(r.json())
pprint.pprint(output_rss)
