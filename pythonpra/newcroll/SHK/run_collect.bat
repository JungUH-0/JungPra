@echo off
rem Run by Windows Task Scheduler.
rem Moves to this folder, runs collectall.py, and appends the output to collect_log.txt.
cd /d "%~dp0"

echo [%date% %time%] run_collect.bat start >> collect_log.txt

rem Use the already downloaded model without an online check, and keep Korean readable in the log.
set HF_HUB_OFFLINE=1
set PYTHONIOENCODING=utf-8

"C:\Users\AISW_203_104\AppData\Local\Programs\Python\Python314\python.exe" collectall.py >> collect_log.txt 2>&1
echo [%date% %time%] run_collect.bat end (exit code %errorlevel%) >> collect_log.txt
echo. >> collect_log.txt
