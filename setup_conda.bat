@echo off
echo Setting up conda environment for Story2Map...

REM Check if conda is installed
where conda >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo conda could not be found. Please install Anaconda or Miniconda first.
    exit /b 1
)

REM Create conda environment from environment.yml
echo Creating conda environment from environment.yml...
call conda env create -f environment.yml

echo.
echo To activate the environment, run:
echo conda activate story2map
echo.
echo For Windows, please download and install Tesseract OCR from:
echo https://github.com/UB-Mannheim/tesseract/wiki
echo.
echo After activating the environment and installing Tesseract OCR,
echo run the application with: streamlit run app.py

pause 