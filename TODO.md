- Write code to EMAIL the newsletter
- Make monkeypatch for date more smart
- Test date limits on newsletter (oy. How?)
- None of the gen_*.py files have test functions.
- The write_transformation() has no test function.


Things to test:
- newsletter max_days settings in config
- Tweets (and toots)
  + construct_tweets based on times
  + scheduling tweets (how to test??)
  + weird date boundaries for the tweet window

- stdout stuff
- writing transformations stuff (do files get put in the correct
  place?)
