echo SEED_KEY="%random%%random%%random%" > seed_key.py

py -3.6-32 -m PyInstaller wwrando.spec --key=%random%%random%%random%
py -3.6-32 build.py

py -3.6-64 -m PyInstaller wwrando.spec --key=%random%%random%%random%
py -3.6-64 build.py
