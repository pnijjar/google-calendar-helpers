#!/usr/bin/env python3

from gcal_helpers import helpers
import tweepy
import datetime, dateutil, pytz
import random
import os
import sys
import subprocess

""" There should be one argument: the name of the file that will be
    tweeted. 

    This is scary! It will tweet whatever is in the config.OUTTWEET
    folder!
"""

global config
config = helpers.load_config('./config-lotsevents.py',caller='send_tweet')

auth = tweepy.OAuthHandler(
  config.TWITTER_CONSUMER_KEY,
  config.TWITTER_CONSUMER_SECRET,
  )
auth.set_access_token(
  config.TWITTER_ACCESS_TOKEN,
  config.TWITTER_ACCESS_SECRET,
  )

# ------- MAIN PROGRAM -------------

api = None

try:
    api = tweepy.API(auth)
except Exception as e:
    helpers.log_msg("send_tweet.py: error opening Twitter API: {}".format(e))
    exit(3)
      
    

#api.update_status("Initializing tweet ability. Expect test tweets...")

#subprocess.call(['logger', "Argument is '{}'".format(config.TWEET_ID)])

tweetfile = os.path.join(config.OUTTWEET, config.TWEET_ID)

# If you can't find the file just fail, I guess?

try:

    with open(tweetfile) as f:
        tweettext = f.readline()
        #helpers.log_msg('ID {}: {}'.format(
        #    config.TWEET_ID,
        #    tweettext,
        #    ))
        api.update_status(tweettext)
        os.remove(tweetfile)

except FileNotFoundError:
    helpers.log_msg('send_tweet.py: Unable to open file {}'.format(tweetfile))
    exit(2)


