set DIST=dist3-64bit
set PYTHONPATH=..\..
set PYTHONUSERBASE=%DIST%
python -m pip wheel -w wheelhouse -r requirements.txt
python -m pip install --prefix=%DIST% --ignore-installed --find-links=wheelhouse --no-index -r requirements.txt
python -m launcher_tool -o %DIST%/poitagger.exe -e poitagger:main --wait-on-error --icon poitagger.ico
python -m launcher_tool.download_python3_minimal -d %DIST%

REM if not exist wheelhouse\pyserial-3.1.1-py2.py3-none-any.whl  python -m pip wheel -w wheelhouse -r requirements.txt
REM python -m launcher_tool -o %DIST%/poitagger.exe --64 -e poitagger:main --icon poitagger.ico 
REM python -m launcher_tool.download_python3_minimal --64 -d %DIST%