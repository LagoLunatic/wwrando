
C:\devkitPro\devkitPPC\bin\powerpc-eabi-as.exe -mregnames -m750cl init_save_with_tweaks.asm -o init_save_with_tweaks.o
if %errorlevel% neq 0 exit /b %errorlevel%
C:\devkitPro\devkitPPC\bin\powerpc-eabi-ld.exe -Ttext 0x803FCFA8 -T linker.ld --oformat binary init_save_with_tweaks.o -o ./init_save_with_tweaks.bin
if %errorlevel% neq 0 exit /b %errorlevel%
del init_save_with_tweaks.o
if %errorlevel% neq 0 exit /b %errorlevel%
