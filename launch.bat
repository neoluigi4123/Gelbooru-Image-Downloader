@echo off

:: Check if Python 3.10 is installed
python --version | findstr /r "3\.10"
if %errorlevel% neq 0 (
    echo Python 3.10 is not installed.
    echo Downloading and installing Python 3.10...
    curl -o python-3.10.exe https://www.python.org/ftp/python/3.10.0/python-3.10.0-amd64.exe
    start /wait python-3.10.exe /quiet InstallAllUsers=1 PrependPath=1
    del python-3.10.exe
)

:: Check if pip is installed
python -m pip --version
if %errorlevel% neq 0 (
    echo pip is not installed.
    echo Installing pip...
    python -m ensurepip --upgrade
)

:: Check and install required libraries
set LIBRARIES=os asyncio aiohttp requests webbrowser tkinter threading
for %%L in (%LIBRARIES%) do (
    python -m pip show %%L >nul 2>&1
    if %errorlevel% neq 0 (
        echo Installing %%L...
        python -m pip install %%L
    )
)

:: Download the "latest" file to determine the latest version of the script
echo Downloading the latest version information...
curl -L -o latest_version.txt https://raw.githubusercontent.com/neoluigi4123/Danbooru-Image-Downloader/main/latest

:: Read the latest version number from the file
set /p VERSION=<latest_version.txt
echo Latest version is %VERSION%

:: Construct the download URL based on the version number
set DOWNLOAD_URL=https://raw.githubusercontent.com/neoluigi4123/Danbooru-Image-Downloader/main/danbooru_%VERSION%.py
echo Downloading %DOWNLOAD_URL%...
curl -L -o danbooru.py %DOWNLOAD_URL%

:: Launch the app
echo Launching danbooru.py...
python danbooru.py
echo Danbooru Image Downloader Launched!

pause
