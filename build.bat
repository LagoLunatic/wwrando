py -3 -m PyInstaller wwrando.spec
@if %errorlevel% neq 0 exit /b %errorlevel%
py -3 build.py
