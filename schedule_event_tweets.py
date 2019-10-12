#!/usr/bin/env python3

from gcal_helpers import helpers
import tweepy
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

# ------- MAIN PROGRAM -------------

#api = tweepy.API(auth)
#api.update_status("Initializing tweet ability. Expect test tweets...")

tweets_to_schedule =  helpers.construct_tweets()
helpers.schedule_tweets(tweets_to_schedule)


"""
Tomorrow, 7:30pm: YWCA - STEM Mentoring. [SHORTURL]. 
[HASHTAGS - WRawesome?]
"""
