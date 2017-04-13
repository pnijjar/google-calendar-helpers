#!/usr/bin/env python3

import config

import requests
import pytz, datetime, dateutil.parser
import jinja2, markdown, html

import pprint


TEMPLATE="rss_template.jinja2"


def get_rfc822_datestring (google_date): 
    """ Convert whatever date Google is using to the RFC-822 dates
        that RSS wants.
    """

    d = dateutil.parser.parse(google_date)

    # Output the proper format
    return d.strftime("%a, %d %b %Y %T %z")


def get_human_datestring (google_date): 
    """ RFC 822 is ugly for humans. Use something nicer. """
    d = dateutil.parser.parse(google_date)
    
    # Wed, Oct 02 2005
    return d.strftime("%a, %b %d %Y, %I:%M %P")

def get_markdown (rawtext): 
    """ Returns escaped markdown of rawtext (which might have had 
        stuff before.
    """
    md = markdown.Markdown() 
    md_text = md.convert(rawtext)
    # esc_text = html.escape(md_text)
    return md_text


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
# (because why should the summary be the title?)
feed_title = cal_dict['summary']


template_loader = jinja2.FileSystemLoader( searchpath=config.TEMPLATE_DIR )
template_env = jinja2.Environment( 
    loader=template_loader,
    autoescape=True,
    )
template_env.filters['rfc822'] = get_rfc822_datestring
template_env.filters['humandate'] = get_human_datestring
template_env.filters['markdown'] = get_markdown


template = template_env.get_template( TEMPLATE ) 
template_vars = { 
  "feed_title": feed_title,
  "feed_description": cal_dict['description'],
  "feed_webmaster" : config.WEBMASTER,
  "feed_webmaster_name" : config.WEBMASTER_NAME,
  "feed_builddate" : time_now.strftime("%a, %d %b %Y %T %z"),
  "feed_pubdate" : cal_dict['updated'],
  "feed_website" : config.WEBSITE,
  "feed_logo_url" : config.LOGO,
  "feed_items" : cal_dict['items'],
  "feed_selflink" : config.FEED_LINK,
  }

output_rss = template.render(template_vars)

outfile = open(config.OUTFILE, "w")
outfile.write(output_rss)


# pprint.pprint(r)
# print("{}".format(r.url))
# pprint.pprint(r.json())
# pprint.pprint(output_rss)
