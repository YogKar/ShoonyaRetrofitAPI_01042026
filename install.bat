@echo off
set REPO_URL=https://github.com/YogKar/ShoonyaRetrofitAPI_01042026.git
set FOLDER_NAME=ShoonyaRetrofit_Live

echo === Starting Shoonya API Installation ===

:: 1. Clone repository
if exist %FOLDER_NAME% (
    echo Removing existing folder...
    rd /s /q %FOLDER_NAME%
)

git clone %REPO_URL% %FOLDER_NAME%
cd %FOLDER_NAME%

:: 2. Install Wheel and Dependencies
echo Installing NorenRestApiPy and dependencies...
py -m pip install *.whl pandas
if exist requirements.txt (
    py -m pip install -r requirements.txt
)

echo ==================================================
echo INSTALLATION COMPLETE!
echo To run the test, use:
echo py Test_Noren_API.py
echo ==================================================
pause
