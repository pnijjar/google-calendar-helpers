#!/usr/bin/env python3

from gcal_helpers import helpers

config = helpers.load_config()
helpers.write_transformation(config, "rss")
