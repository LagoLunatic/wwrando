set /p key= < keys/build_key.txt

py -3.6-32 -m PyInstaller wwrando.spec --key=%key%
py -3.6-32 build.py

py -3.6-64 -m PyInstaller wwrando.spec --key=%key%
py -3.6-64 build.py
