#!/bin/bash

SEND_TWEETS="send_tweet.py"
PYDIR="$1"
VENV_DIR="$2"
CONFFILE="$3"
TWEET_ID="$4"

source ${VENV_DIR}/bin/activate
${PYDIR}/${SEND_TWEETS} --config ${CONFFILE} --tweet-id ${TWEET_ID}
