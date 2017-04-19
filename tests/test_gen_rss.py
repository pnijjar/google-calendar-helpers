#!/usr/bin/env python3

#from gen_rss import gen_rss

# Do the bad thing and import files from the parent folder. 
import sys, os
sys.path.insert(0, os.path.abspath(os.pardir))

import gen_rss

import datetime
import pytest 


# http://stackoverflow.com/questions/23988853/how-to-mock-set-system-date-in-pytest
FAKE_NOW = datetime.datetime(2017, 4, 19, 14, 4, 0)

TEST_GOOGLEDATE = "2016-04-07T20:10.000Z"

TEST_MARKDOWN_SAME = """
<h1>Hello world</h1>

<p>This is a paragraph</p>
"""

TEST_MARKDOWN_PLAIN = """
Hello world
===========

This is a paragraph
"""

@pytest.fixture
def patch_datetime_now(monkeypatch):
    class mydatetime:
        @classmethod
        def now(cls):
            return FAKE_NOW
    monkeypatch.setattr(datetime, 'datetime', mydatetime)


# ==== TEST DATES 

def test_human_date():
    assert gen_rss.get_human_datestring(TEST_GOOGLEDATE) \
        == "Thursday, Apr 07 2016,  8:10pm"

def test_human_dateonly():
    assert gen_rss.get_human_dateonly(TEST_GOOGLEDATE) \
        == "Thursday, Apr 07 2016"

def test_human_rfc822():
    assert gen_rss.get_rfc822_datestring(TEST_GOOGLEDATE) \
        == "Thu, 07 Apr 2016 20:10:00 +0000"


@pytest.mark.xfail(reason="parsedate chokes on 0000")
def test_year_zero():
    assert gen_rss.get_human_date("0000-12-29T00:00.000Z") \
        == "Friday, December 29 0000"



# ==== TEST MARKDOWN 

def test_markdown():
    assert gen_rss.get_markdown(TEST_MARKDOWN_SAME) \
        == TEST_MARKDOWN_SAME.strip()

def test_markdown_markup():
    assert gen_rss.get_markdown(TEST_MARKDOWN_PLAIN).strip() \
        == TEST_MARKDOWN_SAME.strip()



