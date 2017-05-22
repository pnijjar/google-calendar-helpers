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

- Use `virtualenv` to set up a Python 3 environment: `virtualenv -p
  /usr/bin/python3 venv`
- Activate the environment: `venv/bin/activate`
- Install dependencies: `pip install -r requirements.txt`
- Copy `config.py.example` to `config.py` and customize it to your
  needs.
- Run `gen_rss.py`


Caveats
-------

- The code is not production ready. Among other things there is not
  much test coverage. There are no error messages.  
- Because it uses an API key, you can only generate feeds for public
  calendars.
- This project is colonialist: it has only been tested in English, in
  the `America/Toronto` timezone.
- This project sources a file `config.py` that the end user can
  specify on the commandline. This is really dangerous unless you
  trust everybody who can run this script.

