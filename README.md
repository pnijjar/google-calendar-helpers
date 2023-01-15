Generate RSS2 Feeds (and Newsletters) from Google Calendar
========================================

In 2015 Google [dropped
support](https://www.404techsupport.com/2015/10/google-discontinue-feed-google-calendars/)
for RSS feeds from its Calendar product. I am bad at Internet searches
and was not able to find the dozen projects that replace this
functionality, so I wrote my own. 

This is a script that is intended to be run from a cronjob. It is
written in Python 3 with lots of helper modules (requests, jinja2,
dateutil ...). Note that since Google [dropped
support](https://developers.googleblog.com/2018/03/transitioning-google-url-shortener.html)
for its goo.gl shortening service, we are now using the
[pyshorteners](https://github.com/ellisonleao/pyshorteners/) library
for URL shortening. This library is licensed under the GPL3 (which
should be okay, since the Apache 2.0 license is GPL3-compatible). 

There is a second script called `gen_newsletter.py` which will 
create the body of a plaintext email. You can use this to send
newsletters about your events. There is a third script for generating
HTML bullet lists of events, but you probably do not want to use that
one. 

There is a third script that is called `schedule_event_tweets.py`. 
This sends out tweets at random times about upcoming events. It is
moderately dangerous: first it generates tweet text and schedules them
using the `at` command. Then the `at` command launches a second script
which (blindly!) tweets out the contents of the text. Don't use this
one in an untrusted environment. 

There is a fourth script called `gen_sidebar.py` which generates an
HTML bullet list. This is probably not helpful for you, but it can be
used to embed events on a webpage.


Deployment
----------

### Local

- Generate a Google Calendar API key, as described below.
- Use `virtualenv` to set up a Python 3 environment: `virtualenv -p
  /usr/bin/python3 venv`
- Activate the environment: `source venv/bin/activate`
- Install dependencies: `pip install -r requirements.txt`
- Copy `config.py.example` to `config.py` and customize it to your
  needs.
- Run `gen_rss.py` or `gen_newsletter.py` or `gen_sidebar.py` or 
  `schedule_event_tweets.py`

### Generating an API key

- Log into https://console.developers.google.com with a Google account
  (preferably the one that owns the Google calendar in question, but
  it does not really matter).
- Create a new project. 
- Click on `Enable API` (or `Library`). Select the `URL Shortener API`
  and enable it. Do the same for the `Google Calendar API`. 
- Click on `Credentials`, and then `Create Credentials`.
- Create an `API Key`. Give it an appropriate name ("RSS/Newsletter
  key"). Set the restriction to be `IP Addresses`, and enter the IP
  address of the host that will be running the scripts.
  
### Production

- Copy `config.py.example` to `config.py` and customize it to your liking
- Build the docker image with `docker build -t gcal-rss .`
- Run the container and generate the files into a named volume: `docker run --rm -v gcal-rss-data:/data gcal-rss`

Caveats
-------

- The code is probably not production ready (but we are deploying it
  anyways). Among other things there is not
  much test coverage. There are no error messages.  
- Because it uses an API key, you can only generate feeds for public
  calendars.
- This project is colonialist: it has only been tested in English, in
  the `America/Toronto` timezone.
- This project sources a file `config.py` that the end user can
  specify on the commandline. This is really dangerous unless you
  trust everybody who can run this script.
- If you use a person's default calendar the title of the newsletter
  will be the same as their email. The person will have to edit the
  name of the calendar in order for the scripts to display something
  sensible. (This is the "summary" field returned by the API.)
- By default we use the [da.gd](https://da.gd) link shortener for
  newsletters.
