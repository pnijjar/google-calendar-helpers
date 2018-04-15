#!/usr/bin/env python3

import os

# Go to https://console.developers.google.com to generate this. You
# need to enable it for Google Calendar and URL Shortener APIS
API_KEY='Insert-Your-API-key-here'

# Look in your calendar URLs to figure this out (src= parameter). 
#
# This is a list. The first calendar has the master information 
# (such as calendar title and description). Subsequent calendars 
# contribute only events.
CALENDAR_IDS=[
    "nlkc39jt4p0nbc4pk9pj7p5fh0@group.calendar.google.com",
    ]

# How many items should be in the feed? For a busy calendar you want
# this at least 50 (and maybe more). 
NUM_ITEMS='100'

# How many days of events should displayed in the newsletter?
# The NUM_ITEMS setting takes precedence. Use "None" for no limit or a
# positive integer for days. For events only occurring today, use 1.
# eg NEWSLETTER_MAX_DAYS=14
#
# (No, this is not a good idea for RSS feeds. Trust me.)
NEWSLETTER_MAX_DAYS=None


# What link shortening service should be used in newsletters?
# If you have no preference then the default should be okay. 
# If you want to turn off link shortening set: 
# LINK_SHORTENER_PARAMS = None
# 
# See https://github.com/ellisonleao/pyshorteners/ for the 
# syntax of making a new shortener. For example, to 
# use bit.ly, you would specify YOUR_TOKEN, then have: 
# LINK_SHORTENER_PARAMS = {"engine":"Bitly", "bitly_token":YOUR_TOKEN}
#
LINK_SHORTENER_PARAMS = None

# For datetime nonsense 
TIMEZONE='America/Toronto'

# Used as the link field in the RSS feed
WEBSITE='http://watcamp.com'

# Used as the location of this feed
FEED_LINK="{}/watcamp.rss".format(WEBSITE)

# Used as the image for the RSS feed
LOGO="{}/img/logo.png".format(WEBSITE)

# Where to save the output, and what to call it
PARENTDIR=os.path.abspath(os.pardir)
OUTRSS=os.path.join(PARENTDIR, "output", "watcamp.rss")
OUTNEWS=os.path.join(PARENTDIR, "output", "watcamp.txt")
OUTJSON=os.path.join(PARENTDIR, "output", "watcamp.json")
OUTSIDEBAR=os.path.join(PARENTDIR, "output" "watcamp-sidebar.html")

# Who is responsible for this feed
WEBMASTER="admin@example.com"
WEBMASTER_NAME="Webmaster"

# Introductory text for newsletter
NEWSLETTER_HEADER="""
This is the test newsletter.
"""

