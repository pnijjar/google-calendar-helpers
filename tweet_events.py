#!/usr/bin/env python3

from gcal_helpers import helpers
import tweepy
import pprint
import datetime, dateutil, pytz
import jinja2
import random
import os


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

pp = pprint.PrettyPrinter(indent=2)

# --------------------------------
def pick_random_time(start_time, tweet_delta):
    """ Given a start_time (as a Datetime object) and a 
        delta (specified as a datetime.timedelta), 
        produce a new datetime that is randomly selected.
    """

    offset = random.randrange(tweet_delta.seconds)

    return start_time + datetime.timedelta(seconds=offset)


# ---------------------------------
def schedule_tweets(tweets_to_schedule):
    """ Generate tweets, schedule them for random times in the 
        tweet window. Consumes a dict of strings to be tweeted.
    """

    start_dt = dateutil.parser.parse(config.TWEET_WINDOW[0])
    end_dt = dateutil.parser.parse(config.TWEET_WINDOW[1])

    tweet_delta = end_dt - start_dt
    
    # Deal with midnight wraparound (but you should not do this)
    if tweet_delta.days < 0:
        tweet_delta = tweet_delta + datetime.timedelta(days=1)

    # GRRR. NEED SOME TESTS.

    for id in tweets_to_schedule:
        tweet_time = pick_random_time(start_dt, tweet_delta)

        #print("Tweeting at {}: {}".format(
        #  tweet_time,
        #  tweets_to_schedule[id],
        #  ))

        dest_filename = "{}-{}-{}".format(
           tweet_time.strftime("%Y-%m-%dT%H:%M"),
           id,
           random.randrange(1000,10000),
           )
        dest = os.path.join(config.OUTTWEET, dest_filename)

        outfile = open(dest, "w", newline='\r\n', encoding='utf8')
        outfile.write(tweets_to_schedule[id])
        outfile.close()

     
     # at invocation:
     # echo "send_tweet('2019-10-12T04:22--AKH2782dh13e')" \
     #   | at -M 04:22 2019-10-12 
    




# -------------------------------
def construct_tweets():
    """ Generate the text of the tweets. Produce a dict of 
    strings that are the tweet texts.
    """
    results = helpers.call_api()

    # This is actually a datetime, not just a date.
    tz = pytz.timezone(config.TIMEZONE)

    today = helpers.get_time_now()
    today = datetime.datetime(
      today.year,
      today.month,
      today.day,
      0,
      0,
      0,
      0,
      today.tzinfo,
      )

    sorted = helpers.organize_events_by_day(
      results['items'], 
      config.TWEET_NUM_DAYS,
      )

    tweet_output = {} 

    # pp.pprint(sorted)
    for day in sorted:
        
        target_day = dateutil.parser.parse(day)
        target_day = tz.localize(target_day)
        delta = target_day - today
        expression = ""
        #print("\ntoday = {}, target_day = {}, delta = {}\n".format(
        #  today,
        #  target_day,
        #  delta,
        #  ))

        if delta.days in config.TWEET_DATE_EXPRESSION:
            expression = config.TWEET_DATE_EXPRESSION[delta.days]

            for item in sorted[day]:
                tweet_dict = {
                  "summary": item['summary'],
                  "start": item['start'],
                  "htmlLink": item['htmlLink'],
                  "day_expression": expression,
                  }

                tweet_text = helpers.generate_tweet_text(tweet_dict)
                
                tweet_output[item['id']] = tweet_text
                
                # print("{}".format(tweet_text))


    return tweet_output

# ------- MAIN PROGRAM -------------

#api = tweepy.API(auth)

#api.update_status("Initializing tweet ability. Expect test tweets...")

tweets_to_schedule =  construct_tweets()

#pp.pprint(tweets_to_schedule)

#print("-------------------")

schedule_tweets(tweets_to_schedule)


"""
Tomorrow, 7:30pm: YWCA - STEM Mentoring. [SHORTURL]. 
[HASHTAGS - WRawesome?]
"""
