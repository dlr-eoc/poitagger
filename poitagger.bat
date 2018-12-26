@echo off
:: Check for Python Installation
python --version 3 > NUL
if errorlevel 1 goto testPython3
:: Reaching here means Python is installed.
python -m poitagger
:: Once done, exit the batch file -- skips executing the errorNoPython section
goto:eof

:testPython3
python3 --version 3 > NUL
if errorlevel 1 goto errorNoPython
python3 -m poitagger 
goto:eof


:errorNoPython
echo.
echo Error^: Python 3 not found
