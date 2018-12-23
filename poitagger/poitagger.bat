:: Check for Python Installation
python --version 3>NUL
if errorlevel 1 goto errorNoPython

:: Reaching here means Python is installed.
python -m poitagger

:: Once done, exit the batch file -- skips executing the errorNoPython section
goto:eof

:errorNoPython
echo.
echo Error^: Python 3 not installed