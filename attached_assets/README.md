# OpenAI Chatbot

A simple yet powerful chatbot application using Flask and OpenAI's API. This chatbot provides intelligent responses using GPT-3.5-turbo and also offers built-in functions for handling date, time, and basic math questions.

## Features

- OpenAI API integration for AI-powered responses
- Fallback features for basic functionality (time, date, math) without API key
- Web interface with modern UI
- API key management via settings menu
- Environment variable support for deployment configurations

## Setup and Installation

### Prerequisites

- Python 3.7+
- pip (Python package manager)
- OpenAI API key (optional, but recommended for full functionality)

### Local Installation

1. Clone the repository:
   ```
   git clone <repository-url>
   cd chatbot
   ```

2. Create a virtual environment:
   ```
   python -m venv venv
   ```

3. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - macOS/Linux: `source venv/bin/activate`

4. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

5. Create a `.env` file (copy from `.env.example`):
   ```
   cp .env.example .env
   ```

6. Edit the `.env` file to add your OpenAI API key (optional)

7. Start the application:
   ```
   python main.py
   ```

8. Open your browser and navigate to `http://127.0.0.1:5000/`

## Deployment Options

### Deploying to Heroku

1. Make sure you have the Heroku CLI installed:
   ```
   npm install -g heroku
   ```

2. Login to Heroku:
   ```
   heroku login
   ```

3. Create a new Heroku app:
   ```
   heroku create your-chatbot-name
   ```

4. Push to Heroku:
   ```
   git push heroku main
   ```

5. Set your OpenAI API key as an environment variable (optional):
   ```
   heroku config:set OPENAI_API_KEY=your_api_key_here
   ```

6. Open your app:
   ```
   heroku open
   ```

### Deploying to Render

1. Create a new Web Service on Render
2. Connect your repository
3. Set the following configuration:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn main:app`
4. Add your environment variables (including `OPENAI_API_KEY` if desired)
5. Deploy

### Deploying to Digital Ocean App Platform

1. Create a new App on Digital Ocean App Platform
2. Connect your repository
3. Set environment variables
4. Deploy your app

## API Endpoints

- `GET /`: Main chatbot interface
- `POST /get_response`: Get a response from the chatbot (requires JSON body with "message" field)
- `GET /check_api_key`: Check if the API key is configured
- `POST /set_api_key`: Set or update the API key

## Usage

1. Visit the web interface
2. Type your message in the input field
3. Press Enter or click the Send button
4. To set up your OpenAI API key, click the ⚙️ icon and enter your key

## License

MIT

## Acknowledgements

- OpenAI for the GPT API
- Flask team for the web framework
