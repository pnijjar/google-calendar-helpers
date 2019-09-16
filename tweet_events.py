#!/usr/bin/env python3

from gcal_helpers import helpers
import tweepy

conf = helpers.load_config()

auth = tweepy.OAuthHandler(
  conf.TWITTER_CONSUMER_KEY,
  conf.TWITTER_CONSUMER_SECRET,
  )
auth.set_access_token(
  conf.TWITTER_ACCESS_TOKEN,
  conf.TWITTER_ACCESS_SECRET,
  )

api = tweepy.API(auth)

api.update_status("Initializing tweet ability. Expect test tweets...")
