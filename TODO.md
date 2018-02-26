- Write code to EMAIL the newsletter
- Make monkeypatch for date more smart
- Make monkeypatch for URL shortener return a fail message instead of
  just the longurl
- Test date limits on newsletter (oy. How?)
- Move away from config.py into command line parsing
- Turn config.py into config.ini, which is less unsafe
- Change the gen_* files to do the argument parsing, instead of doing
  it in load_config. Then I can specify the type of transformation
  too. 
- None of the gen_*.py files have test functions.
- The write_transformation() has no test function.

