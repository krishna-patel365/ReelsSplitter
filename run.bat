@echo off
setlocal
cd /d "%~dp0"

REM Prefer the Python 3.13 installation if present, otherwise use the Python launcher.
set "PY="
set "USE_LAUNCHER=0"
if exist "%ProgramFiles%\Python314\python.exe" set "PY=%ProgramFiles%\Python314\python.exe"
if not defined PY if exist "%LocalAppData%\Programs\Python\Python313\python.exe" set "PY=%LocalAppData%\Programs\Python\Python313\python.exe"
if not defined PY (
  where py >nul 2>nul
  if not errorlevel 1 set "USE_LAUNCHER=1"
)
if not defined PY if "%USE_LAUNCHER%"=="0" (
  echo Python was not found. Install Python from https://www.python.org/downloads/windows/
  pause
  exit /b 1
)

if "%USE_LAUNCHER%"=="1" (
  py -3 -c "import tkinter" >nul 2>nul
) else (
  "%PY%" -c "import tkinter" >nul 2>nul
)
if errorlevel 1 (
  echo Tkinter is missing from the selected Python.
  echo Repair Python and enable Tcl/Tk and IDLE in optional features.
  pause
  exit /b 1
)

if "%USE_LAUNCHER%"=="1" (
  py -3 -c "import PIL" >nul 2>nul
) else (
  "%PY%" -c "import PIL" >nul 2>nul
)
if errorlevel 1 (
  echo Installing Pillow for the selected Python...
  if "%USE_LAUNCHER%"=="1" (
    py -3 -m pip install --user Pillow
  ) else (
    "%PY%" -m pip install --user Pillow
  )
  if errorlevel 1 (
    echo Pillow installation failed. Install it for the selected Python.
    pause
    exit /b 1
  )
)

where ffmpeg >nul 2>nul
if errorlevel 1 (
  echo FFmpeg was not found in PATH. Ensure ffmpeg.exe is on PATH.
  pause
  exit /b 1
)
where ffprobe >nul 2>nul
if errorlevel 1 (
  echo FFprobe was not found in PATH. Ensure ffprobe.exe is on PATH.
  pause
  exit /b 1
)

if "%USE_LAUNCHER%"=="1" (
  py -3 "%~dp0bin\app.py"
) else (
  "%PY%" "%~dp0bin\app.py"
)
if errorlevel 1 (
  echo.
  echo The application stopped with an error. Read the traceback above.
  pause
)
