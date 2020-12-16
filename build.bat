py -3.8-32 -m PyInstaller wwrando.spec
if %errorlevel% neq 0 exit /b %errorlevel%
py -3.8-32 build.py
if %errorlevel% neq 0 exit /b %errorlevel%

py -3.8 -m PyInstaller wwrando.spec
if %errorlevel% neq 0 exit /b %errorlevel%
py -3.8 build.py
if %errorlevel% neq 0 exit /b %errorlevel%
