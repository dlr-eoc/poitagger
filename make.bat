set DIST=dist3-64bit
set PYTHONPATH=..\..
set PYTHONUSERBASE=%DIST%
REM if not exist wheelhouse\pyserial-3.1.1-py2.py3-none-any.whl  python -m pip wheel -w wheelhouse -r requirements.txt
python -m launcher_tool -o %DIST%/poitagger.exe --64 -e poitagger:main --icon poitagger.ico 
python -m launcher_tool.download_python3_minimal --64 -d %DIST%