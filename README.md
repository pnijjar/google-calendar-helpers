Generate RSS2 Feeds (and Newsletters) from Google Calendar
========================================

In 2015 Google [dropped
support](https://www.404techsupport.com/2015/10/google-discontinue-feed-google-calendars/)
for RSS feeds from its Calendar product. I am bad at Internet searches
and was not able to find the dozen projects that replace this
functionality, so I wrote my own. 

This is a script that is intended to be run from a cronjob. It is
written in Python 3 with lots of helper modules (requests, jinja2,
dateutil ...). 

There is a second script called `gen_newsletter.py` which will 
create the body of a plaintext email. You can use this to send
newsletters about your events.


Deployment
----------

- Generate a Google Calendar API key, as described below.
- Use `virtualenv` to set up a Python 3 environment: `virtualenv -p
  /usr/bin/python3 venv`
- Activate the environment: `source venv/bin/activate`
- Install dependencies: `pip install -r requirements.txt`
- Copy `config.py.example` to `config.py` and customize it to your
  needs.
- Run `gen_rss.py`

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

