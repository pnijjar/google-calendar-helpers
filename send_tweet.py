#!/usr/bin/env python3

from gcal_helpers import helpers

config = helpers.load_config(caller='send_tweet')
helpers.send_tweet(config)

