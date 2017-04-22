#!/usr/bin/env python3

# Do the bad thing and import files from the parent folder. 
import sys, os
sys.path.insert(0, os.path.abspath(os.pardir))

import gen_rss

import datetime, pytz, dateutil.tz
import pytest 
import os
import json


# ==== CONSTANTS

MD_IN = "data_markdown_in"
MD_OUT = "data_markdown_out"

JSON_IN = "data_json_in"
RSS_OUT = "data_rss_out"

TMPDIR = "/tmp/pytest-temp"

# ==== TEST DATA

# http://stackoverflow.com/questions/23988853/how-to-mock-set-system-date-in-pytest
# Wow this is fragile, though. It assumes that every test case will
# have the same generation time. 
# In the RSS, set 
# <lastBuildDate>Wed, 19 Apr 2017 15:01:56 -0400</lastBuildDate>
FAKE_NOW = datetime.datetime(
    2017, 4, 19, 
    15, 1, 56, 
    tzinfo=dateutil.tz.tzoffset(None, -14400)
    )

RSS_EXAMPLES = [ 
    "01-fullcalendar",  # Full complicated output
    "02-one-event", 
    ]


MARKDOWN_EXAMPLES = [
    "01-identity",
    "02-header",
    ]

# Format: googledate, rfc822, human, human-dateonly, 
# explanation
# This is because I am testing many different 
# functions with the same input.
DATE_EXAMPLES = [
    ("2016-04-07T20:10.000Z", 
        "Thu, 07 Apr 2016 20:10:00 +0000",
        "Thursday, Apr 07 2016,  8:10pm",
        "Thursday, Apr 07 2016",
        "Regular date with UTC",
        ),
    ("2017-04-07T20:10.000EDT", 
        "Fri, 07 Apr 2017 20:10:00 -0400",
        "Friday, Apr 07 2017,  8:10pm",
        "Friday, Apr 07 2017",
        "Regular date with EDT",
        ),
    ("1970-01-01T00:00.000Z", 
        "Thu, 01 Jan 1970 00:00:00 +0000",
        "Thursday, Jan 01 1970, 12:00am",
        "Thursday, Jan 01 1970",
        "Start of epoch",
        ),
    ("2016-04-07T23:59.000Z", 
        "Thu, 07 Apr 2016 23:59:00 +0000",
        "Thursday, Apr 07 2016, 11:59pm",
        "Thursday, Apr 07 2016",
        "Final minute",
        ),
    ]



# ==== Helper Functions 

def save_to_temp(filename, output):
    """ Save output to a tempdir so I can generate 
        outputs.
    """

    # Does the temp dir exist?
    # Let's hope it is not just a file.
    if not os.path.isdir(TMPDIR):
        os.makedirs(TMPDIR)

    filepath = os.path.join(TMPDIR, filename)
    with open(filepath, "w") as f: 
        f.write(output)



def pickdate(target, datelist):
    """ Pick the date from a list of tuples.
        target: an index > 1
    """

    return list(
        map(
            lambda x : (x[0], x[target]),
            datelist
            )
        )

@pytest.fixture
def patch_datetime_now(monkeypatch):
    class mydatetime:
        @classmethod
        # Gah. I have to account for timezone input.
        def now(cls, tz=pytz.timezone('America/Toronto')):
            return FAKE_NOW
    monkeypatch.setattr(datetime, 'datetime', mydatetime)


def get_testfile_path(filename, datadir, ext=""):
    """ ext should be something like ".html"
    """

    fullfile = "{}{}".format(filename,ext)
    return os.path.join(
        os.path.dirname(__file__),
        datadir,
        fullfile,
        )

def get_file_as_string(filename, datadir, ext=""):
    filepath = get_testfile_path(filename, datadir, ext)

    with open(filepath, "r") as f:
        filetext = f.read()

    return filetext
    

def get_markdown_files(testname):
    intext = get_file_as_string(testname, MD_IN, ".md")
    outtext = get_file_as_string(testname, MD_OUT, ".html")

    return (intext, outtext)
    

def get_rss_files(testname):
    jsontext = get_file_as_string(testname, JSON_IN, ".json")
    jsondict = json.loads(jsontext)

    rsstext = get_file_as_string(testname, RSS_OUT, ".rss")
    return (jsondict, rsstext)

    

# ==== TEST DATES 

@pytest.mark.parametrize(
    "googledate, target",
    pickdate(2, DATE_EXAMPLES),
    )
def test_human_date(googledate, target):
    assert gen_rss.get_human_datestring(googledate) \
        == target

@pytest.mark.parametrize(
    "googledate, target",
    pickdate(3, DATE_EXAMPLES),
    )
def test_human_dateonly(googledate, target):
    assert gen_rss.get_human_dateonly(googledate) \
        == target

@pytest.mark.parametrize(
    "googledate, target",
    pickdate(1, DATE_EXAMPLES),
    )
def test_rfc822(googledate, target):
    assert gen_rss.get_rfc822_datestring(googledate) \
        == target

@pytest.mark.xfail(reason="parsedate chokes on 0000")
def test_year_zero():
    assert gen_rss.get_human_date("0000-12-29T00:00.000Z") \
        == "Friday, December 29 0000"



# ==== TEST MARKDOWN 

@pytest.mark.parametrize(
    "testcase", 
    MARKDOWN_EXAMPLES,
    )
def test_markdown(testcase):
    (intext, outtext) = get_markdown_files(testcase)
    assert gen_rss.get_markdown(intext) == outtext


# ==== TEST JSON CONVERSION

@pytest.mark.parametrize(
    "testcase",
    RSS_EXAMPLES,
    )
def test_json_to_rss(testcase, patch_datetime_now):
    (injson, outrss) = get_rss_files(testcase)
    testrss = gen_rss.generate_rss(injson)
    
    try: 
        assert testrss == outrss
    except AssertionError:
        # Use this to generate output for future runs
        save_to_temp("{}.rss".format(testcase), testrss)    
        raise

