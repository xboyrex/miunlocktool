@echo off
title XBOYREX Unlock Studio — Windows EXE Builder
color 0C
echo ============================================================================
echo              X B O Y R E X   W I N D O W S   E X E   B U I L D E R
echo            Developed by xboyrex (Mayank Droid) - v8.1 Official
echo ============================================================================
echo.
cd /d "%~dp0"
pip install -U pyinstaller customtkinter packaging ntplib darkdetect pytz urllib3 icmplib requests
pyinstaller --noconfirm --onefile --windowed --icon="res\app_icon.ico" --add-data "res;res" --name "XBOYREX_Unlock_Studio_v8.1" 8.1.py
echo.
echo [✔] Build Complete! EXE is inside: %~dp0dist\XBOYREX_Unlock_Studio_v8.1.exe
pause
