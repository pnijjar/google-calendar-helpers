#!/usr/bin/env python3

from gcal_helpers import helpers
import tweepy
import pprint
import datetime, dateutil, pytz
import jinja2


global config
config = helpers.load_config('./config-lotsevents.py')

auth = tweepy.OAuthHandler(
  config.TWITTER_CONSUMER_KEY,
  config.TWITTER_CONSUMER_SECRET,
  )
auth.set_access_token(
  config.TWITTER_ACCESS_TOKEN,
  config.TWITTER_ACCESS_SECRET,
  )


def construct_tweets():
    """ Generate the text of the tweets and save the files to
    TWEETQUEUE
    """
    results = helpers.call_api()

    # This is actually a datetime, not just a date.
    today = helpers.get_time_now()
    tz = pytz.timezone(config.TIMEZONE)

    pp = pprint.PrettyPrinter(indent=2)
    #pp.pprint(results)

    sorted = helpers.organize_events_by_day(
      results['items'], 
      config.TWITTER_EVENT_CUTOFF,
      )

    # pp.pprint(sorted)
    for day in sorted:
        
        target_day = dateutil.parser.parse(day)
        target_day = tz.localize(target_day)
        delta = target_day - today
        expression = ""

        if delta.days in config.TWEET_DATE_EXPRESSION:
            expression = config.TWEET_DATE_EXPRESSION[delta.days]

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

                tweet_text = helpers.generate_tweet_text(tweet_dict)
                print("{}".format(tweet_text))



# ------- MAIN PROGRAM -------------

#api = tweepy.API(auth)

#api.update_status("Initializing tweet ability. Expect test tweets...")

construct_tweets()


"""
Tomorrow, 7:30pm: YWCA - STEM Mentoring. [SHORTURL]. 
[HASHTAGS - WRawesome?]
"""
