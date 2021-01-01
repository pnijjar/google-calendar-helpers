#!/usr/bin/env python3

import requests
import pytz, datetime, dateutil.parser
import jinja2, markdown, html
import collections
import argparse, sys, os
import pyshorteners
import pyshorteners.exceptions
from .liteshort import Shortener as lss
import random
import subprocess
import tweepy
import pprint
import json
from bs4 import BeautifulSoup


RSS_TEMPLATE="rss_template.jinja2"
NEWSLETTER_TEMPLATE="newsletter_template.jinja2"
SIDEBAR_TEMPLATE="sidebar_template.jinja2"
TWEET_TEMPLATE="tweet_template.jinja2"
INVALID_DATE="1969-12-12T23:59.000Z"
TEMPLATE_DIR=os.path.dirname(os.path.abspath(__file__))
LAUNCH_TWEET_SCRIPT='launch_tweet_sender.sh'

# ------------------------------
def load_config(configfile=None, caller=None):
    """ Load configuration definitions.
       (This is really scary, actually. We are trusting that the 
       config.py we are taking as input is sane!) 

       If both the commandline and the parameter are 
       specified then the commandline takes precedence.
    """

    # '/home/pnijjar/watcamp/python_rss/gcal_helpers/config.py'
    # See: http://www.karoltomala.com/blog/?p=622
    DEFAULT_CONFIG_SOURCEFILE = os.path.join(
        os.getcwd(),
        'config.py',
        )

    config_location=None

    if configfile: 
        config_location=configfile
    else: 
        config_location = DEFAULT_CONFIG_SOURCEFILE


    # Now parse commandline options (Here??? This code smells bad.)
    parser = argparse.ArgumentParser(
        description="Generate fun RSS/newsletter feeds from "
            "Google Calendar entries.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        )
    parser.add_argument('-c', '--configfile', 
        help='configuration file location',
        default=config_location,
        )

    # HACK HACK HACK. send_tweet needs to load the config file, 
    # but needs an additional parameter. 

    if caller == 'send_tweet':
        parser.add_argument('--tweet-id',
            help='ID of file containing tweet',
            required=True,
            )

    args = parser.parse_args()
    if args.configfile:
        config_location = os.path.abspath(args.configfile)


    # http://stackoverflow.com/questions/11990556/python-how-to-make-global
    global config

    # Blargh. You can load modules from paths, but the syntax is
    # different depending on the version of python. 
    # http://stackoverflow.com/questions/67631/how-to-import-a-mod
    # https://stackoverflow.com/questions/1093322/how-do-i-ch

    if sys.version_info >= (3,5): 
        import importlib.util 
        spec = importlib.util.spec_from_file_location(
            'config',
            config_location,
            )
        config = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(config)
    elif sys.version_info >= (3,3):
        # This is the only one I can test. Sad!
        from importlib.machinery import SourceFileLoader
        config = SourceFileLoader( 'config', config_location,).load_module()
    else:
        import imp
        config = imp.load_source( 'config', config_location,)

    if caller == 'send_tweet' and args.tweet_id:
        config.TWEET_ID = args.tweet_id

    # Needed to send tweets
    config.CONFIG_LOCATION = config_location

    # For test harness
    return config
            

# ------------------------------
def log_msg(msg, toscreen=False):
   """ Log a message to syslog.
   """

   subprocess.call(['logger', msg])

   if toscreen:
       print(msg)


# ------------------------------
def print_from_template (s): 
    """ Show the value of a string that is being processed in a 
        Jinja template, for debugging.
    """
    print(s)
    return s


# ------------------------------
def get_rfc822_datestring (google_date): 
    """ Convert whatever date Google is using to the RFC-822 dates
        that RSS wants.
    """

    # Sometimes dates look like "0000-12-29T00:00.000Z" and this
    # confuses the date parser...
    d = dateutil.parser.parse(google_date)

    # Output the proper format
    return d.strftime("%a, %d %b %Y %T %z")


# ------------------------------
def get_human_datestring (google_date): 
    """ RFC 822 is ugly for humans. Use something nicer. """

    d = dateutil.parser.parse(google_date)
    
    # Wednesday, Oct 02 2005, 8:00pm
    return d.strftime("%A, %b %d %Y, %l:%M%P")

# ------------------------------
def get_human_dateonly (google_date):
    """ If there is no minute defined then the date looks bad.
    """

    d = dateutil.parser.parse(google_date)
    
    # Wednesday, Oct 02 2005
    return d.strftime("%A, %b %d %Y")

# ------------------------------
def get_short_human_dateonly (google_date):
    """ Readable by humans, but shorter. """

    d = dateutil.parser.parse(google_date)

    # Sun, Feb 18
    return d.strftime("%a, %b %e")

# ------------------------------
def get_short_human_datetime (google_date):
    """ Date time readable by humans, but shorter. """

    d = dateutil.parser.parse(google_date)

    # Sun, Feb 18, 8:00pm
    return d.strftime("%a, %b %e, %l:%M%P")


# ------------------------------
def get_human_timeonly (google_date):
    """ Forget the date. Just gimme the time"""

    d = dateutil.parser.parse(google_date)
    #  8:00pm
    return d.strftime("%l:%M%P")


# ------------------------------
def extract_datestring (gcal_event):
    """ Given a google calendar event dictionary, 
        grab either the datetime string or the date string.
    """
    #print("gcal_event: {}".format(gcal_event))

    try:

        if 'dateTime' in gcal_event['start']:
            retval = gcal_event['start']['dateTime']
        elif 'date' in gcal_event['start']:
            retval = gcal_event['start']['date']
        else:
            # This should never happen. Maybe an exception is wrong?
            print("Uh oh. extract_datestring could not find a date.")
            retval = None

    except:
        raise Exception("bad extract_datestring: "
                        "gcal_event = '{}'".format(
                           gcal_event))




    return retval


# ------------------------------
def add_timezone(google_url):
    """ Given a Google Calendar URL, append an argument for the 
        timezone string.
    """

    return "{}&ctz={}".format(google_url, config.TIMEZONE)

# ------------------------------
def get_underline (title, underline_char):
    """ Given a string and a character (a string of length 1, 
        although this is not enforced), return an "underline" 
        consisting of the character repeated the same length 
        as the title. 

        title had better not be None. 
    """

    return underline_char * len(title) 


# ------------------------------
def get_markdown (rawtext): 
    """ Returns escaped markdown of rawtext (which might have had 
        stuff before.
    """
    md = markdown.Markdown() 
    md_text = md.convert(rawtext)
    # esc_text = html.escape(md_text)
    return md_text

# ------------------------------
def get_time_now():
   
    target_timezone = pytz.timezone(config.TIMEZONE)
    time_now = datetime.datetime.now(tz=target_timezone)

    return time_now

# ------------------------------
def call_api():
    """ Returns JSON from API call, or some error I won't handle."""

    time_now = get_time_now()

    # Format looks like: 2017-03-25T00:00:00-0500
    time_now_formatted = time_now.strftime("%Y-%m-%dT%H:%M:%S%z")

    master_json = None

    for id in config.CALENDAR_IDS:

        api_url='https://www.googleapis.com/calendar/v3/calendars/{}/events'.format(id)

        api_params = { 
            'maxResults' : config.NUM_ITEMS,
            'orderBy' : 'startTime',
            'singleEvents' : 'true',
            'key' : config.API_KEY,
            'timeMin' : time_now_formatted,
            } 

        r = requests.get(api_url, params=api_params)
        r.raise_for_status()

        calendar_json = r.json()

        if master_json is None:
            master_json = calendar_json
        else:
            # Append items from this calendar to the master 
            master_items = master_json['items']
            new_items = calendar_json['items']
            
            master_json['items'] = master_items + new_items

    return master_json

# ------------------------------
def shorten_url(longurl):
    """ Shortens URL using a given service. Yay surveillance.
    """
    retval = longurl

    s = pyshorteners.Shortener()

    if config.LINK_SHORTENER_SERVICE:

        if config.LINK_SHORTENER_SERVICE in s.available_shorteners:
            #print("Looks like {} is available.".format(
            #  config.LINK_SHORTENER_SERVICE,
            #  ))

            svc = config.LINK_SHORTENER_SERVICE

            if config.LINK_SHORTENER_PARAMS:
                params = config.LINK_SHORTENER_PARAMS
                s = pyshorteners.Shortener(**params)
          
            try:
                retval = s.__getattr__(svc).short(longurl)

                #print("Got short url {}".format(
                #  retval,
                #  ))

            except pyshorteners.exceptions.ShorteningErrorException:
                retval = longurl

        # this is a hack because Liteshort is not an official
        # pyshorteners implementation. (I guess I could submit
        # it, but I am afraid).
        #
        # The parameter "domain" is mandatory for this shortener.
        elif config.LINK_SHORTENER_SERVICE == 'liteshort':
            s = lss(**config.LINK_SHORTENER_PARAMS)

            try:
                retval = s.short(longurl)

            except pyshorteners.exceptions.ShorteningErrorException as e:
                #print("ShorteningError: {}", e)
                retval = longurl

    # I won't handle this. Let the program crash.
    # except pyshorteners.exceptions.UnknownShortenerException:
    #    retval = "%s (Error: %s)" % \
    #               (longurl, 
    #               "Incorrect shortening service invocation?")

    return retval


# ------------------------------
def organize_events_by_day(
    cal_items,
    max_days=None,
    ):
    """ Given a JSON formatted set of events, sort it into a list of lists
        (?) with events sorted by starting day and time. 

        If max_days > 0 then only include events taking place within 
        max_days. (1 == today)
    """

    # print("Max days is: {}".format(max_days))

    # I think python really wants me to make this a dict, so that 
    # there is title metadata. But that means we have to sort twice.
    outdict = collections.OrderedDict()

    lastdate = get_human_dateonly(INVALID_DATE)
    today = get_time_now()
    
    # Set the time to midnight
    today = today.replace(hour=0, minute=0, second=0)
    # print ("today is {}".format(today))

    for event in sorted(cal_items, key=extract_datestring,):
        
        this_datestring = extract_datestring(event)
        this_datetime = dateutil.parser.parse(this_datestring)
        
        # @bug Bah. If this_datetime is only a date then it is naive. 
        # Then you cannot subtract the date properly. 
        # This will cause all kinds of edge-case nonsense that might 
        # mean entries get skipped. 

        # Check if this date is naive. 
        # http://stackoverflow.com/questions/5802108/
        
        tz = pytz.timezone(config.TIMEZONE)
        if this_datetime.tzinfo is None: 
            #print ("{}: tzinfo is {}".format(
            #    this_datetime, 
            #    this_datetime.tzinfo
            #    ))
            this_datetime = tz.localize(this_datetime)
        elif this_datetime.tzinfo.utcoffset(this_datetime) is None:
            #print ("{}: tzinfo.utcoffset is {}".format(
            #    this_datetime, 
            #    this_datetime.tzinfo.utcoffset(this_datetime)
            #    ))
            this_datetime = tz.localize(this_datetime)
           
        thisdate = get_human_dateonly(this_datestring)

        # Skip this entry if it is too far in the future
        if max_days is not None:
            date_delta = this_datetime - today
            if date_delta.days >= max_days:
                continue
            #else:
            #    print("{} has delta {}".format(
            #        this_datetime,
            #        date_delta,
            #        ))


        if thisdate != lastdate:
            outdict[thisdate] = [] 
            lastdate = thisdate

        outdict[thisdate].append(event)


    return outdict



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

        send_tweet_cmd = "{}/{} {} {} {} {}".format(
          config.SHELL_SCRIPT_DIR,
          LAUNCH_TWEET_SCRIPT,
          config.PYDIR,
          config.VENV_DIR,
          config.CONFIG_LOCATION,
          dest_filename,
          )

        at_time = tweet_time.strftime("%H:%M")
        at_date = tweet_time.strftime("%Y-%m-%d")
          
        # https://stackoverflow.com/questions/8475290/how-do-i-write-to-a-python-subprocess-stdin
        p = subprocess.Popen(
          ['at', '-M', at_time, at_date], 
          stdout = subprocess.PIPE,
          stdin = subprocess.PIPE,
          stderr = subprocess.PIPE,
          )
        retval = p.communicate(input=send_tweet_cmd.encode())

        # I do not know how to identify failure. Huh.
        #if retval != 0: 
        #    log_msg("{}: failed to start at command.  Retval={}".format(
        #      sys.argv[0],
        #      retval,
        #      ), True)

     
     # at invocation:
     # echo "send_tweet('2019-10-12T04:22--AKH2782dh13e')" \
     #   | at -M 04:22 2019-10-12 
    

# -------------------------------
def construct_tweets():
    """ Generate the text of the tweets. Produce a dict of 
    strings that are the tweet texts.
    """
    results = call_api()

    # This is actually a datetime, not just a date.
    tz = pytz.timezone(config.TIMEZONE)

    today = get_time_now()

    # Ugh. Need to convert this to midnight, or 
    # delta calculations can break. 
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

    sorted = organize_events_by_day(
      results['items'], 
      config.TWEET_NUM_DAYS,
      )

    tweet_output = {} 

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
                # Most watcamp entries start with a link to the event.
                # Use that if it is available. Otherwise link to 
                # the calendar.

                soup = BeautifulSoup(item['description'], 'html.parser')

                link_to_tweet = shorten_url(
                  add_timezone(item['htmlLink'])
                  )

                # soup.a == first link
                if soup.a:
                    href = soup.a['href']
                    text = soup.a.contents[0]

                    if href == text:
                        link_to_tweet = soup.a['href']


                tweet_dict = {
                  "summary": item['summary'],
                  "start": item['start'],
                  "htmlLink": link_to_tweet,
                  "day_expression": expression,
                  }

                tweet_text = generate_tweet_text(tweet_dict)
                
                tweet_output[item['id']] = tweet_text
                
                # print("{}".format(tweet_text))


    return tweet_output


# -------------------------------
def generate_tweet_text(tweet_dict):
    """ Given information to put in a tweet, generate the string to
        tweet out. 
    """

    
    template_loader = jinja2.FileSystemLoader(
        searchpath=TEMPLATE_DIR
        )
    template_env = jinja2.Environment( 
        loader=template_loader,
        lstrip_blocks=True,
        trim_blocks=True,
        )
    template_env.filters['humandate'] = get_short_human_datetime
    template_env.filters['humandateonly'] = get_short_human_dateonly
    template_env.filters['timeonly'] = get_human_timeonly

    template = template_env.get_template( TWEET_TEMPLATE ) 
    template_vars = { 
      "event" : tweet_dict,
      }

    tweet_text = template.render(template_vars)

    return tweet_text


# ------------------------------
def generate_newsletter(cal_dict):
    """ Given a JSON formatted calendar dictionary, make the text for 
        a fascinating newsletter.
    """

    sorted_items = organize_events_by_day(
        cal_dict['items'],
        config.NEWSLETTER_MAX_DAYS,
        )
    # pprint.pprint(sorted_items)


    template_loader = jinja2.FileSystemLoader(
        searchpath=TEMPLATE_DIR,
        )
    template_env = jinja2.Environment(
        loader=template_loader,
        lstrip_blocks=True,
        trim_blocks=True,
        )
    template_env.filters['humandate'] = get_human_datestring
    template_env.filters['humandateonly'] = get_human_dateonly
    template_env.filters['timeonly'] = get_human_timeonly
    template_env.filters['shorturl'] = shorten_url
    template_env.filters['underline'] = get_underline
    template_env.filters['addtz'] = add_timezone

    template = template_env.get_template( NEWSLETTER_TEMPLATE ) 
    template_vars = { 
      "title": cal_dict['summary'],
      "items" : sorted_items,
      "header" : config.NEWSLETTER_HEADER,
      }

    output_newsletter = template.render(template_vars)
    return output_newsletter



# ------------------------------
def generate_rss(cal_dict):
    """ Given a JSON formatted calendar dictionary, make and return 
        the RSS file.
    """


    # --- Process template 

    template_loader = jinja2.FileSystemLoader(
        searchpath=TEMPLATE_DIR
        )
    template_env = jinja2.Environment( 
        loader=template_loader,
        autoescape=True,
        )
    template_env.filters['rfc822'] = get_rfc822_datestring
    template_env.filters['humandate'] = get_human_datestring
    template_env.filters['humandateonly'] = get_human_dateonly
    template_env.filters['markdown'] = get_markdown
    template_env.filters['print'] = print_from_template

    time_now = get_time_now()

    template = template_env.get_template( RSS_TEMPLATE ) 
    template_vars = { 
      "feed_title": config.RSS_TITLE,
      "feed_description": config.DESCRIPTION,
      "feed_webmaster" : config.WEBMASTER,
      "feed_webmaster_name" : config.WEBMASTER_NAME,
      "feed_builddate" : time_now.strftime("%a, %d %b %Y %T %z"),
      "feed_pubdate" : cal_dict['updated'],
      "feed_website" : config.WEBSITE,
      "feed_logo_url" : config.LOGO,
      "feed_items" : cal_dict['items'],
      "feed_selflink" : config.FEED_LINK,
      }

    output_rss = template.render(template_vars)

    return output_rss


# ------------------------------
def generate_sidebar(cal_dict):
    """ Given a JSON formatted calendar dictionary, make and return 
        the HTML sidebar list.
    """

    # --- Process template 

    template_loader = jinja2.FileSystemLoader(
        searchpath=TEMPLATE_DIR
        )
    template_env = jinja2.Environment( 
        loader=template_loader,
        autoescape=True,
        )
    template_env.filters['humandate'] = get_short_human_datetime
    template_env.filters['humandateonly'] = get_short_human_dateonly
    template_env.filters['addtz'] = add_timezone

    time_now = get_time_now()

    template = template_env.get_template( SIDEBAR_TEMPLATE ) 
    template_vars = { 
      "feed_items" : cal_dict['items'],
      }

    output_sidebar = template.render(template_vars)

    return output_sidebar

# ------------------------------
def send_tweet():
    """ Open Tweepy and send the tweet.
    """

    load_config(caller='send_tweet')

    auth = tweepy.OAuthHandler(
      config.TWITTER_CONSUMER_KEY,
      config.TWITTER_CONSUMER_SECRET,
      )
    auth.set_access_token(
      config.TWITTER_ACCESS_TOKEN,
      config.TWITTER_ACCESS_SECRET,
      )

    api = None

    try:
        api = tweepy.API(auth)
    except Exception as e:
        log_msg("send_tweet.py: error opening Twitter API: {}".format(e))
        exit(3)

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
        log_msg('send_tweet.py: Unable to open file {}'.format(tweetfile))
        exit(2)


# ------------------------------
def write_transformation(transform_type):
    """ Write a file for the transformation. The transform_type should
        be one of "rss", "newsletter", or "sidebar". If I was a better
        programmer then I would force this.
    """

    load_config() 

    # Before generating the new RSS get rid of the old one. 
    dest = None
    if transform_type == "rss":
        dest = config.OUTRSS

    elif transform_type == "newsletter":
        dest = config.OUTNEWS

    elif transform_type == "sidebar":
        dest = config.OUTSIDEBAR

    elif transform_type == 'tweets':
        # Grr. This does not really fit in.
        tweets_to_schedule = construct_tweets()
        schedule_tweets(tweets_to_schedule)
        return
    else:
        raise NameError("Incorrect type '%s' listed" %
          (transform_type,))
    
    if os.path.isfile(dest):
        os.remove(dest)

    if os.path.isfile(config.OUTJSON):
        os.remove(config.OUTJSON)

    cal_json = call_api() 

    outjson = open(config.OUTJSON, "w", encoding='utf8')
    json.dump(cal_json, outjson, indent=2, separators=(',', ': '))

    generated_file = None

    if transform_type == "rss":
        generated_file = generate_rss(cal_json)

    elif transform_type == "newsletter":
        generated_file = generate_newsletter(cal_json)

    elif transform_type == "sidebar":
        generated_file = generate_sidebar(cal_json)

    # No else should be needed. 
    # print("dest is: {}".format(dest))

    # Insert Windows newlines for dumb email clients
    outfile = open(dest, "w", newline='\r\n', encoding='utf8')
    outfile.write(generated_file)




# ------------------------------
if __name__ == '__main__':

    #cal_json = call_api() 

    #outjson = open(config.OUTJSON, "w")
    #json.dump(cal_json, outjson, indent=2, separators=(',', ': '))

    # cal_rss = generate_rss(cal_json)
    # print(cal_rss)

    #outfile = open(config.OUTFILE, "w")
    #outfile.write(cal_rss)

    #events = cal_json['items']
    #d = organize_events_by_day(events)

    #for i in d:
    #    print(i)


    write_newsletter()
   

# pprint.pprint(r)
# print("{}".format(r.url))
# pprint.pprint(r.json())
# pprint.pprint(output_rss)
