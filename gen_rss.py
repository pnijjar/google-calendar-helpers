#!/usr/bin/env python3

import config

import requests
import pytz, datetime, dateutil.parser
import jinja2, markdown, html

import pprint
import json


RSS_TEMPLATE="rss_template.jinja2"
NEWSLETTER_TEMPLATE="newsletter_template.jinja2"

def print_from_template (s): 
    """ Show the value of a string that is being processed in a 
        Jinja template, for debugging.
    """
    print(s)
    return s


def get_rfc822_datestring (google_date): 
    """ Convert whatever date Google is using to the RFC-822 dates
        that RSS wants.
    """

    # Sometimes dates look like "0000-12-29T00:00.000Z" and this
    # confuses the date parser...
    d = dateutil.parser.parse(google_date)

    # Output the proper format
    return d.strftime("%a, %d %b %Y %T %z")


def get_human_datestring (google_date): 
    """ RFC 822 is ugly for humans. Use something nicer. """

    d = dateutil.parser.parse(google_date)
    
    # Wednesday, Oct 02 2005, 8:00pm
    return d.strftime("%A, %b %d %Y, %l:%M%P")

def get_human_dateonly (google_date):
    """ If there is no minute defined then the date looks bad.
    """

    d = dateutil.parser.parse(google_date)
    
    # Wednesday, Oct 02 2005
    return d.strftime("%A, %b %d %Y")


def get_markdown (rawtext): 
    """ Returns escaped markdown of rawtext (which might have had 
        stuff before.
    """
    md = markdown.Markdown() 
    md_text = md.convert(rawtext)
    # esc_text = html.escape(md_text)
    return md_text

def get_time_now():
   
    target_timezone = pytz.timezone(config.TIMEZONE)
    time_now = datetime.datetime.now(tz=target_timezone)

    return time_now

def call_api():
    """ Returns JSON from API call, or some error I won't handle."""

    time_now = get_time_now()

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

    calendar_json = r.json()

    return calendar_json

def generate_newsletter(cal_dict):
    """ Given a JSON formatted calendar dictionary, make the text for 
        a fascinating newsletter.
    """
    template_loader = jinja2.FileSystemLoader(
        searchpath=config.TEMPLATE_DIR,
        )
    template_env = jinja2.Environment(
        loader=template_loader,
        lstrip_blocks=True,
        trim_blocks=True,
        )
    template_env.filters['humandate'] = get_human_datestring
    template_env.filters['humandateonly'] = get_human_dateonly

    template = template_env.get_template( NEWSLETTER_TEMPLATE ) 
    template_vars = { 
      "title": cal_dict['summary'],
      "items" : cal_dict['items'],
      "header" : config.NEWSLETTER_HEADER,
      }



    output_newsletter = template.render(template_vars)
    return output_newsletter



def generate_rss(cal_dict):
    """ Given a JSON formatted calendar dictionary, make and return 
        the RSS file.
    """


    # --- Process template 

    # This is kind of sketchy in general
    # (because why should the summary be the title?)
    feed_title = cal_dict['summary']


    template_loader = jinja2.FileSystemLoader(
        searchpath=config.TEMPLATE_DIR
        )
    template_env = jinja2.Environment( 
        loader=template_loader,
        autoescape=True,
        )
    template_env.filters['rfc822'] = get_rfc822_datestring
    template_env.filters['humandate'] = get_human_datestring
    template_env.filters['humandateonly'] = get_human_dateonly
    template_env.filters['markdown'] = get_markdown
    template_env.filters['print'] = print_from_template


    time_now = get_time_now()

    template = template_env.get_template( RSS_TEMPLATE ) 
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

    return output_rss



if __name__ == '__main__':

    cal_json = call_api() 

    outjson = open(config.OUTJSON, "w")
    json.dump(cal_json, outjson, indent=2, separators=(',', ': '))

    cal_rss = generate_newsletter(cal_json)
    print(cal_rss)

    outfile = open(config.OUTFILE, "w")
    outfile.write(cal_rss)



# pprint.pprint(r)
# print("{}".format(r.url))
# pprint.pprint(r.json())
# pprint.pprint(output_rss)
