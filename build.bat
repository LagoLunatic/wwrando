set /p key= < keys/build_key.txt

py -3.6-32 -m PyInstaller wwrando.spec --key=%key%
if %errorlevel% neq 0 exit /b %errorlevel%
py -3.6-32 build.py
if %errorlevel% neq 0 exit /b %errorlevel%

py -3.6 -m PyInstaller wwrando.spec --key=%key%
if %errorlevel% neq 0 exit /b %errorlevel%
py -3.6 build.py
if %errorlevel% neq 0 exit /b %errorlevel%
