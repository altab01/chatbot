@echo off
ECHO Setting up ChatBot Environment...

REM Create virtual environment
python -m venv venv

REM Activate virtual environment
CALL venv\Scripts\activate.bat

REM Upgrade pip
python -m pip install --upgrade pip

REM Install dependencies
pip install -r requirements.txt

REM Create .env file from example if it doesn't exist
IF NOT EXIST .env (
    COPY .env.example .env
    ECHO Created .env file from template.
    ECHO Please edit .env to add your OpenAI API key.
)

ECHO Setup complete!
ECHO To start the chatbot, run 'start.bat'
PAUSE 