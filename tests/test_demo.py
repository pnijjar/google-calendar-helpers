#!/usr/bin/env python3

#from gen_rss import gen_rss

import sys, os
sys.path.insert(0, os.path.abspath(os.pardir))

import gen_rss

def test_human_date():
    assert gen_rss.get_human_datestring("2016-04-01T20:00:00") \
        == "Friday, Apr 01 2016,  8:00pm"
