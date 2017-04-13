#!/usr/bin/env python3

import config

import requests
import pytz, datetime, dateutil.parser
import jinja2, markdown, html

import pprint


TEMPLATE="/home/pnijjar/watcamp/python_rss/rss_template.jinja2"



def get_rfc822_datestring (google_date): 
    """ Convert whatever date Google is using to the RFC-822 dates
        that RSS wants.
    """

    # This is actually wrong because it ignores timezone.
    # See: http://stackoverflow.com/questions/19472859
    d = dateutil.parser.parse(google_date)

    # Output the proper format
    return d.strftime("%a, %d %b %Y %T %z")


def get_human_datestring (google_date): 
    """ RFC 822 is ugly for humans. Use something nicer. """
    d = dateutil.parser.parse(google_date)
    
    # Wed, Oct 02 2005
    return d.strftime("%a, %b %d %Y, %I:%M %P")

def get_escaped_markdown (rawtext): 
    """ Returns escaped markdown of rawtext (which might have had 
        stuff before.
    """
    md = markdown.Markdown() 
    md_text = md.convert(rawtext)
    esc_text = html.escape(md_text)
    return esc_text


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
template_env = jinja2.Environment( 
    loader=template_loader,
    autoescape=True,
    )
template_env.filters['rfc822'] = get_rfc822_datestring
template_env.filters['humandate'] = get_human_datestring
template_env.filters['emarkdown'] = get_escaped_markdown


# https://gist.github.com/glombard/7554134
# I want this filter to insert <p> tags into the text
md = markdown.Markdown()
template_env.filters['markdown'] = lambda t: jinja2.Markup(md.convert(t))


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
