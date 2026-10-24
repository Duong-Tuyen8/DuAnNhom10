@echo off
cd /d %~dp0frontend
echo Mo file index.html bang trinh duyet:
echo   start http://localhost:8000
echo.
echo Neu mo truc tiep, dung Live Server cua VS Code.
start "" "%~dp0frontend\index.html"
pause