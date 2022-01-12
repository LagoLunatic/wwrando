py -3.9 -m PyInstaller wwrando.spec
if %errorlevel% neq 0 exit /b %errorlevel%
py -3.9 build.py
if %errorlevel% neq 0 exit /b %errorlevel%
