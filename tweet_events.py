#!/usr/bin/env python3

from gcal_helpers import helpers
import tweepy
import pprint
import datetime, dateutil, pytz
import jinja2

TWITTER_EVENT_CUTOFF=8
# Next week

config = helpers.load_config('./config-lotsevents.py')

auth = tweepy.OAuthHandler(
  config.TWITTER_CONSUMER_KEY,
  config.TWITTER_CONSUMER_SECRET,
  )
auth.set_access_token(
  config.TWITTER_ACCESS_TOKEN,
  config.TWITTER_ACCESS_SECRET,
  )

DATE_EXPRESSION = { 
  0: "Today!",
  3: "Three sleeps!",
  5: "Five sleeps!",
  6: "Next week!"
  }

TWEET_TEMPLATE="tweet_template.jinja2"

# -------------------------------
def generate_tweet_text(tweet_dict):
    """ Given information to put in a tweet, generate the string to
        tweet out. 
    """

    
    template_loader = jinja2.FileSystemLoader(
        searchpath=helpers.TEMPLATE_DIR
        )
    template_env = jinja2.Environment( 
        loader=template_loader,
        lstrip_blocks=True,
        trim_blocks=True,
        )
    template_env.filters['humandate'] = helpers.get_short_human_datetime
    template_env.filters['humandateonly'] = helpers.get_short_human_dateonly
    template_env.filters['addtz'] = helpers.add_timezone
    template_env.filters['shorturl'] = helpers.shorten_url
    template_env.filters['timeonly'] = helpers.get_human_timeonly

    template = template_env.get_template( TWEET_TEMPLATE ) 
    template_vars = { 
      "event" : tweet_dict,
      }

    tweet_text = template.render(template_vars)

    return tweet_text


# ------- MAIN PROGRAM -------------

#api = tweepy.API(auth)

#api.update_status("Initializing tweet ability. Expect test tweets...")

results = helpers.call_api()

# This is actually a datetime, not just a date.
today = helpers.get_time_now()
tz = pytz.timezone(config.TIMEZONE)

pp = pprint.PrettyPrinter(indent=2)
#pp.pprint(results)

sorted = helpers.organize_events_by_day(results['items'], TWITTER_EVENT_CUTOFF)

# pp.pprint(sorted)
for day in sorted:
    
    target_day = dateutil.parser.parse(day)
    target_day = tz.localize(target_day)
    delta = target_day - today
    expression = ""

    if delta.days in DATE_EXPRESSION:
        expression = DATE_EXPRESSION[delta.days]

        print("\n\nDay: {} - {} (delta = {})\n==============\n".format(
          day, 
          expression,
          delta.days,
          ))

        for item in sorted[day]:
            tweet_dict = {
              "summary": item['summary'],
              "start": item['start'],
              "htmlLink": item['htmlLink'],
              "day_expression": expression,
              }

            tweet_text = generate_tweet_text(tweet_dict)
            print("{}".format(tweet_text))

# Want: summary, datetime start, htmlLink, location?
"""
Tomorrow, 7:30pm: YWCA - STEM Mentoring. [SHORTURL]. 
[HASHTAGS - WRawesome?]
"""
