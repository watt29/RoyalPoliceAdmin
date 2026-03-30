@echo off
title Smart Police Bot Terminator
color 0c
echo ==============================================
echo        Stopping Smart Police Report Bot
echo ==============================================
echo.
echo Searching for background Bot processes...
wmic process where "name='python.exe' and commandline like '%%main_bot.py%%'" call terminate >nul 2>&1
echo.
echo [ SUCCESS ] Bot stopped!
echo.
timeout /t 3
