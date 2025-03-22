@echo off
ECHO Starting ChatBot Application...

REM Activate virtual environment if it exists
IF EXIST venv\Scripts\activate.bat (
    CALL venv\Scripts\activate.bat
)

REM Install dependencies
pip install -r requirements.txt

REM Start the application
python main.py

PAUSE 