pip3 install pywin32-ctypes==0.1.2
@if %errorlevel% neq 0 exit /b %errorlevel%
pip3 install PyInstaller
@if %errorlevel% neq 0 exit /b %errorlevel%
install_dependencies.bat
