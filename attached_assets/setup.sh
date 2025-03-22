#!/bin/bash

echo "Setting up ChatBot Environment..."

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt

# Create .env file from example if it doesn't exist
if [ ! -f .env ]; then
    cp .env.example .env
    echo "Created .env file from template."
    echo "Please edit .env to add your OpenAI API key."
fi

echo "Setup complete!"
echo "To start the chatbot, run 'bash start.sh'" 