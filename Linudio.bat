@echo off
setlocal
cd /d "%~dp0"
title Linudio

rem Use the project's virtual environment if there is one (backend\venv or backend\.venv).
if exist "backend\venv\Scripts\activate.bat" call "backend\venv\Scripts\activate.bat"
if exist "backend\.venv\Scripts\activate.bat" call "backend\.venv\Scripts\activate.bat"

rem Close anything left over from a previous run (the API on 8000, the web UI on 3000).
call :free_ports

rem First run: install the Node packages (root tooling, then the frontend).
if not exist "node_modules" (
    echo Installing Node packages...
    call npm install || goto :fail
)
if not exist "frontend\node_modules" (
    echo Installing frontend packages...
    pushd frontend
    call npm install || goto :fail
    popd
)

rem Open the browser as soon as both servers answer. This runs in the background.
start "" /b powershell -NoProfile -WindowStyle Hidden -Command "$deadline=(Get-Date).AddMinutes(5); foreach($u in 'http://localhost:8000','http://localhost:3000'){ while((Get-Date) -lt $deadline){ try { Invoke-WebRequest $u -UseBasicParsing -TimeoutSec 120 | Out-Null; break } catch { Start-Sleep -Seconds 1 } } }; Start-Process 'http://localhost:3000'"

rem Tells the backend to stop itself (and with it, everything) once the last browser tab is closed.
set LINUDIO_EXIT_ON_CLOSE=1

echo Starting Linudio. Close the browser tab to stop it.
call npm run dev

rem Normally reached after the tab is closed; make sure nothing is left behind.
call :free_ports
exit /b 0

:fail
echo.
echo Something went wrong. See the messages above.
pause
exit /b 1

:free_ports
powershell -NoProfile -Command "foreach($p in 8000,3000){ Get-NetTCPConnection -LocalPort $p -State Listen -ErrorAction SilentlyContinue | ForEach-Object { taskkill /PID $_.OwningProcess /T /F | Out-Null } }"
exit /b 0
