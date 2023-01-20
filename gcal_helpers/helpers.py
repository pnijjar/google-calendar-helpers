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
import yaml


RSS_TEMPLATE="rss_template.jinja2"
NEWSLETTER_TEMPLATE="newsletter_template.jinja2"
SIDEBAR_TEMPLATE="sidebar_template.jinja2"
TWEET_TEMPLATE="tweet_template.jinja2"
INVALID_DATE="1969-12-12T23:59.000Z"

# This is the folder that contains the helper.py script
TEMPLATE_DIR=os.path.dirname(os.path.abspath(__file__))

# This should be the folder that has send_tweet.py
LAUNCH_PYDIR=os.path.abspath(os.path.join(TEMPLATE_DIR, os.pardir))

# This should be the folder that has the shell script
SHELL_SCRIPT_DIR=os.path.abspath(
 os.path.join(TEMPLATE_DIR, 'scripts')
 )

TWEET_SHELL_SCRIPT='launch_tweet_sender.sh'

SUPPORTED_TRANSFORMS=['rss','newsletter','sidebar','tweets']


## -----------------------------
class UnsupportedTransformError(ValueError):
    pass




## ------------------------------
def parse_args(caller = None):
    """ Parse commandline args. Return the args thingy. (What is it?
    A module? It is like a dict.)

    caller: The calling program? Currently: 'send_tweet'
    """

    # Now parse commandline options (Here??? This code smells bad.)
    parser = argparse.ArgumentParser(
        description="Generate fun RSS/newsletter feeds from "
            "Google Calendar entries.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        )
    parser.add_argument('-c', '--configfile', 
        help='configuration file location',
        required=True,
        )


    # HACK HACK HACK. send_tweet needs to load the config file, 
    # but needs an additional parameter. 

    if caller == 'send_tweet':
        parser.add_argument('--tweet-id',
            help='ID of file containing tweet',
            required=True,
            )

    args = parser.parse_args()

    return args


## ------------------------------
def load_config_yaml(configfile=None):
    """ Load config definitions from YAML file.

    I feel the commandline arg should be mandatory?

    Return the config dict. It can be global later.

    """
    with open(configfile, encoding='utf-8') as f:
        config = yaml.load(f, Loader=yaml.SafeLoader)

    if not config.get('flags'):
        config['flags'] = {}

    if not config.get('internal'):
        config['internal'] = {}

    return config


# ------------------------------
def load_config(configfile=None, caller=None):
    """ Load configuration definitions.

       :param configfile : a configfile with YAML to load. If this 
         is specified then no commandline args are parsed.
       :param caller : What calls this. 'send_tweet' is defined.
       :returns the config dict

    """
    configuration_lala = None
    args = None

    if configfile:
        configuration_lala = load_config_yaml(configfile)
    else: 
        args = parse_args(caller)
        configfile = args.configfile
        configuration_lala = load_config_yaml(configfile)

    configuration_lala['internal']['config_location'] \
      = os.path.abspath(configfile)

    if caller == 'send_tweet' and args.tweet_id:
        config['flags']['tweet_id'] = args.tweet_id

    # For test harness
    return configuration_lala
            

# ------------------------------
# XXX - replace with proper logging
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
def add_timezone(config, google_url):
    """ Given a Google Calendar URL, append an argument for the 
        timezone string.
    """

    return "{}&ctz={}".format(google_url, config['feeds']['timezone'])

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
def get_time_now(config):
   
    target_timezone = pytz.timezone(config['feeds']['timezone'])
    time_now = datetime.datetime.now(tz=target_timezone)

    return time_now

# ------------------------------
def call_api(config):
    """ Returns JSON from API call, or some error I won't handle."""

    time_now = get_time_now(config)

    # Format looks like: 2017-03-25T00:00:00-0500
    time_now_formatted = time_now.strftime("%Y-%m-%dT%H:%M:%S%z")

    master_json = None

    for id in config['services']['google']['calendar_ids']:

        api_url='https://www.googleapis.com/calendar/v3/calendars/{}/events'.format(id)

        api_params = { 
            'maxResults' : config['feeds']['num_items'],
            'orderBy' : 'startTime',
            'singleEvents' : 'true',
            'key' : config['services']['google']['api_key'],
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
def shorten_url(config, longurl):
    """ Shortens URL using a given service. Yay surveillance.
    """
    retval = longurl

    s = pyshorteners.Shortener()

    if config['services']['shortener']['service']:

        s_config = config['services']['shortener']

        if s_config['service'] in s.available_shorteners:

            svc = s_config['service']

            if s_config['params']:
                # This variable should not be needed. :(
                # I am bad at Python.
                params = s_config['params']
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
        elif s_config['service'] == 'liteshort':
            s = lss(**s_config['params'])

            try:
                retval = s.short(longurl)

            except pyshorteners.exceptions.ShorteningErrorException as e:
                #print("ShorteningError: {}", e)
                retval = longurl

        elif s_config['service'] == 'no_shortener':
            reval = longurl

    # I won't handle this. Let the program crash.
    # except pyshorteners.exceptions.UnknownShortenerException:
    #    retval = "%s (Error: %s)" % \
    #               (longurl, 
    #               "Incorrect shortening service invocation?")

    return retval


# ------------------------------
def organize_events_by_day(
    config,
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
    today = get_time_now(config)
    
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
        
        tz = pytz.timezone(config['feeds']['timezone'])
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
def schedule_tweets(config, tweets_to_schedule):
    """ Generate tweets, schedule them for random times in the 
        tweet window. Consumes a dict of strings to be tweeted.
    """
    t_config = config['feeds']['tweets']

    start_dt = dateutil.parser.parse(t_config['window']['start'])
    end_dt = dateutil.parser.parse(t_config['window']['end'])

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
        dest = os.path.join(
          config['paths']['tweet_cache_path'], 
          dest_filename
          )

        outfile = open(dest, "w", newline='\r\n', encoding='utf8')
        outfile.write(tweets_to_schedule[id])
        outfile.close()

        # XXX - Paths need to get fixed here
        send_tweet_cmd = "{}/{} {} {} {} {}".format(
          SHELL_SCRIPT_DIR,
          TWEET_SHELL_SCRIPT,
          LAUNCH_PYDIR,
          config['paths']['venv_path'],
          config['internal']['config_location'],
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
def construct_tweets(config):
    """ Generate the text of the tweets. Produce a dict of 
    strings that are the tweet texts.
    """
    results = call_api(config)

    # This is actually a datetime, not just a date.
    tz = pytz.timezone(config['feeds']['timezone'])

    today = get_time_now(config)

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
      config,
      results['items'], 
      config['feeds']['tweets']['days_in_advance'],
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

        if delta.days in config['feeds']['tweets']['date_expression']:
            expression = \
              config['feeds']['tweets']['date_expression'][delta.days]

            for item in sorted[day]:
                # Most watcamp entries start with a link to the event.
                # Use that if it is available. Otherwise link to 
                # the calendar.

                soup = BeautifulSoup(item['description'], 'html.parser')

                link_to_tweet = shorten_url(
                  config,
                  add_timezone(config, item['htmlLink'])
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
def generate_newsletter(config, cal_dict):
    """ Given a JSON formatted calendar dictionary, make the text for 
        a fascinating newsletter.
    """

    sorted_items = organize_events_by_day(
        config,
        cal_dict['items'],
        config['feeds']['newsletter']['max_days']
        )
    # pprint.pprint(sorted_items)

    shorten_url_curry = lambda x: shorten_url(config, x)
    add_timezone_curry = lambda x: add_timezone(config, x)


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
    template_env.filters['shorturl'] = shorten_url_curry
    template_env.filters['underline'] = get_underline
    template_env.filters['addtz'] = add_timezone_curry

    template = template_env.get_template( NEWSLETTER_TEMPLATE ) 
    template_vars = { 
      "title": cal_dict['summary'],
      "items" : sorted_items,
      "header" : config['feeds']['newsletter']['header']
      }

    output_newsletter = template.render(template_vars)
    return output_newsletter


def filter_duplicate_guids(events):
    seen = set()
    filtered = []
    for event in events:
        guid = event['iCalUID']
        if guid in seen:
            continue
        filtered.append(event)
        seen.add(guid)

    return filtered


def sort_by_date(events):
    return sorted(events, key=lambda event: event['start'].get('dateTime', event['start'].get('date', '')))


# ------------------------------
def generate_rss(config, cal_dict):
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

    time_now = get_time_now(config)

    """

    Filtering duplicate events: Repeated events have the same calendar
    UID, resulting in an invalid RSS feed as feeds are not allowed to
    have multiple `<item>`s with the same `<guid>` tag. Filtering them
    out allows us to still list the _next_ iteration of that
    particular event though.
    
    Sorting by date: Because we're ingesting several calendars, the
    RSS feed will end up being ordered first by the arbitrary order of
    the calendar IDs in the config and then by the date (Google's API
    already sorts them by date). At this point we have several date
    sorted lists. To get a properly sorted RSS feed we need to go
    ahead and actually sort the full list of events by date, which we
    can do easily via the ISO formated date time stamps.

    """
    cal_dict['items'] = sort_by_date(filter_duplicate_guids(cal_dict['items']))

    feed_selflink = config['feeds']['rss']['url']
    if config['feeds']['rss']['relative_to_website']:
        feed_selflink = "{}/{}.rss".format(
          config['feeds']['website'],
          config['feeds']['rss']['url'],
        )
      

    template = template_env.get_template( RSS_TEMPLATE ) 
    template_vars = { 
      "feed_title": config['feeds']['rss']['title'],
      "feed_description": config['feeds']['rss']['description'],
      "feed_webmaster" : config['feeds']['webmaster'],
      "feed_webmaster_name" : config['feeds']['webmaster_name'],
      "feed_builddate" : time_now.strftime("%a, %d %b %Y %T %z"),
      "feed_pubdate" : cal_dict['updated'],
      "feed_website" : config['feeds']['website'],
      "feed_logo_url" : config['feeds']['logo_url'],
      "feed_items" : cal_dict['items'],
      "feed_selflink" : feed_selflink,
      }

    output_rss = template.render(template_vars)

    return output_rss


# ------------------------------
def generate_sidebar(config, cal_dict):
    """ Given a JSON formatted calendar dictionary, make and return 
        the HTML sidebar list.
    """

    # --- Process template 
    add_timezone_curry = lambda x: add_timezone(config, x)

    template_loader = jinja2.FileSystemLoader(
        searchpath=TEMPLATE_DIR
        )
    template_env = jinja2.Environment( 
        loader=template_loader,
        autoescape=True,
        )
    template_env.filters['humandate'] = get_short_human_datetime
    template_env.filters['humandateonly'] = get_short_human_dateonly
    template_env.filters['addtz'] = add_timezone_curry

    time_now = get_time_now(config)

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

    # This is going to break! We need the credentials in a file!
    config = load_config(caller='send_tweet')
    t_config = config['services']['twitter']

    auth = tweepy.OAuthHandler(
      t_config['consumer_key'],
      t_config['consumer_secret'],
      )
    auth.set_access_token(
      t_config['access_token'],
      t_config['access_secret'],
      )

    api = None

    try:
        api = tweepy.API(auth)
    except Exception as e:
        log_msg("send_tweet.py: error opening Twitter API: {}".format(e))
        exit(3)

    tweetfile = os.path.join(
      config['paths']['tweet_cache_path'],
      config['flags']['tweet_id'],
      )

    # If you can't find the file just fail, I guess?
    try:
        with open(tweetfile) as f:
            tweettext = f.readline()
            #helpers.log_msg('ID {}: {}'.format(
            #    config['flags']['tweet_id'],
            #    tweettext,
            #    ))
            api.update_status(tweettext)
            os.remove(tweetfile)

    except FileNotFoundError:
        log_msg('send_tweet.py: Unable to open file {}'.format(tweetfile))
        exit(2)


# ------------------------------
def write_transformation(config, transforms):
    """ Write a file for the transformation. The transforms should
        should be a LIST containing a subset of SUPPORTED_TRANSFORMS.
        Note that SUPPORTED_TRANSFORMS must match the keys under the
        'feeds' entry in the YAML (currently 'rss', 'newsletter',
        'sidebar', 'tweets')
    """

    for t in transforms:
        if not (t in SUPPORTED_TRANSFORMS):
            raise UnsupportedTransformError(
              "{} is not a supported transformation! "
              "Supported transforms:"
              " {}".format( t, SUPPORTED_TRANSFORMS,)
              )

    cal_json = call_api(config) 

    # Keep JSON?
    if config['paths']['cache_file'].get('name'):
        json_filename = config['paths']['cache_file']['name']

        cache_dir = ""
        if config['paths']['cache_file'].get('relative_to_cache_path'):
            cache_dir = config['paths']['cache_path']

        out_json_file=os.path.join(cache_dir, json_filename)


        if os.path.isfile(out_json_file):
            os.remove(out_json_file)

        outjson = open(out_json_file, "w", encoding='utf8')
        json.dump(cal_json, outjson, indent=2, separators=(',', ': '))
   



    for transform_type in transforms:


        generated_file = None


        if transform_type == "rss":
            generated_file = generate_rss(config, cal_json)

        elif transform_type == "newsletter":
            generated_file = generate_newsletter(config, cal_json)

        elif transform_type == "sidebar":
            generated_file = generate_sidebar(config, cal_json)

        elif transform_type == 'tweets':
            # Grr. This does not really fit in.
            tweets_to_schedule = construct_tweets(config)
            schedule_tweets(config, tweets_to_schedule)
            return


        if transform_type in ['rss', 'newsletter', 'sidebar']:
            if config['feeds'][transform_type]['filename'] == 'stdout':
                print(generated_file)
            else:
                folder = ''
                info = config['feeds'][transform_type]
                if info.get('relative_to_publish_path'):
                    folder = config['paths']['publish_path']

                filebase = info['filename']

                dest = os.path.join(folder, filebase)
        
                if os.path.isfile(dest):
                    os.remove(dest)

                # Insert Windows newlines for dumb email clients
                outfile = open(dest, "w", newline='\r\n', encoding='utf8')
                outfile.write(generated_file)


# ------------------------------
if __name__ == '__main__':

    write_newsletter()
   

