py -3.10 -m PyInstaller --log-level=WARN wwrando.spec
if %errorlevel% neq 0 exit /b %errorlevel%
py build.py
if %errorlevel% neq 0 exit /b %errorlevel%
