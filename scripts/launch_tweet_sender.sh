#!/bin/bash

CONFDIR="/home/pnijjar/src/google-calendar-helpers"
PYDIR="/home/pnijjar/src/google-calendar-helpers"
SEND_TWEETS="send_tweet.py"
CONFFILE="$1"
TWEET_ID="$2"

source $PYDIR/venv/bin/activate
${PYDIR}/${SEND_TWEETS} --config ${CONFFILE} --tweet-id ${TWEET_ID}
