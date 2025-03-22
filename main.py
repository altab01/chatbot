import os
import string
import datetime
import re
import math
import json
from flask import Flask, request, jsonify, render_template, send_from_directory
from openai import OpenAI, OpenAIError

# Load environment variables from .env file if it exists
try:
    from dotenv import load_dotenv
    load_dotenv()  # take environment variables from .env
    print("Loaded environment variables from .env file")
except ImportError:
    print("python-dotenv not installed, using existing environment variables")

# Initialize the Flask app with static folder
app = Flask(__name__, static_folder="static", static_url_path="/static")

# Create a simple OpenAI Client - with a fallback to None if no API key is available
try:
    # Try to initialize the OpenAI client
    client = OpenAI()
    # Test the API key by attempting a simple call
    api_key_set = os.environ.get("OPENAI_API_KEY") is not None
except (OpenAIError, ImportError) as e:
    print(f"OpenAI client initialization failed: {e}")
    client = None
    api_key_set = False

# Fallback functions for when API is not available
def get_date():
    now = datetime.datetime.now()
    # Format: Monday, January 1, 2023
    return now.strftime("%A, %B %d, %Y")

def get_time():
    now = datetime.datetime.now()
    # Format: 3:45 PM
    return now.strftime("%I:%M %p")

def calculate_math(message):
    # Remove any text, leaving only the math expression
    math_expression = re.sub(r'[a-zA-Z]', '', message)
    math_expression = math_expression.strip()
    
    try:
        # Use eval safely with basic operations
        allowed_chars = set('0123456789+-*/().^ ')
        if not all(c in allowed_chars for c in math_expression):
            return "I can only handle basic math operations: +, -, *, /, ^, (), and numbers."
        
        # Replace ^ with ** for exponentiation
        math_expression = math_expression.replace('^', '**')
        
        # Evaluate the expression
        result = eval(math_expression)
        return f"The result of {math_expression.replace('**', '^')} is {result}"
    except Exception as e:
        return "Sorry, I couldn't solve that math problem. Make sure it's a valid expression."

def get_ai_response(message):
    """Get a response from OpenAI API."""
    try:
        # First check if we should use our local functions for certain queries
        lower_message = message.lower()
        
        # Check for date-related queries
        if any(word in lower_message for word in ["date", "today", "day"]):
            return f"Today's date is {get_date()}."
            
        # Check for time-related queries
        if any(word in lower_message for word in ["time", "hour", "clock"]):
            return f"The current time is {get_time()}."
        
        # Check for direct math expressions
        if re.match(r'^[\d\+\-\*\/\(\)\^\s]+$', message):
            return calculate_math(message)
            
        # If API key is available and client is initialized, use OpenAI
        if client and api_key_set:
            # The newest OpenAI model is "gpt-4o" which was released May 13, 2024.
            # Do not change this unless explicitly requested by the user
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a helpful, friendly, and concise assistant. Provide short and direct answers to user questions."},
                    {"role": "user", "content": message}
                ],
                max_tokens=250  # Allowing slightly longer responses
            )
            return response.choices[0].message.content
        else:
            # Fallback if no API key is available
            return "To use the AI features, please set your OpenAI API key in the settings menu (⚙️). For now, I can only handle basic date, time, and math questions."
    
    except Exception as e:
        print(f"Error with OpenAI API: {e}")
        return "I encountered an error while processing your request. You might need to check your API key or connection."

@app.route('/')
def home():
    # Add static_url_path to serve assets from static folder
    return render_template('index.html')

@app.route('/get_response', methods=['POST'])
def chatbot_response():
    try:
        data = request.get_json()
        message = data.get('message', '')
        if not message:
            return jsonify({"response": "Please send a message."})
        
        # Get AI response
        response = get_ai_response(message)
        return jsonify({"response": response})
    
    except Exception as e:
        print(f"Error in API: {e}")
        return jsonify({"response": "I'm having trouble processing that right now. Please try again later."})

@app.route('/check_api_key', methods=['GET'])
def check_api_key():
    """Endpoint to check if API key is configured"""
    if api_key_set:
        return jsonify({"status": "API key is configured"})
    else:
        return jsonify({"status": "API key is not configured", 
                        "message": "Set your API key in the settings menu (⚙️) to use the OpenAI API features."})

@app.route('/set_api_key', methods=['POST'])
def set_api_key():
    """Endpoint to set API key (not for production use)"""
    global client, api_key_set
    
    try:
        data = request.get_json()
        api_key = data.get('api_key', '')
        if not api_key:
            return jsonify({"status": "error", "message": "No API key provided"})
        
        # This only sets the key for the current session and is not secure for production
        os.environ["OPENAI_API_KEY"] = api_key
        
        # Update the client with the new key
        try:
            client = OpenAI(api_key=api_key)
            # Make a test call to verify the API key works
            client.models.list(limit=1)
            api_key_set = True
            return jsonify({"status": "success", "message": "API key set successfully"})
        except Exception as e:
            print(f"Error setting OpenAI API key: {e}")
            os.environ.pop("OPENAI_API_KEY", None)
            api_key_set = False
            return jsonify({"status": "error", "message": f"Invalid API key or OpenAI API error: {str(e)}"})
            
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

if __name__ == '__main__':
    # Get port from environment variable or default to 5000
    port = int(os.environ.get("PORT", 5000))
    
    # Set host to 0.0.0.0 to make it accessible from outside
    host = os.environ.get("HOST", "0.0.0.0")
    
    # Determine if we're in debug mode (not recommended for production)
    debug_mode = os.environ.get("DEBUG", "False").lower() == "true"
    
    print("Starting the chatbot server...")
    print(f"OpenAI API Key {'is' if api_key_set else 'is NOT'} configured.")
    print(f"Server running at http://{host}:{port}/ (locally: http://127.0.0.1:{port}/)")
    print("Click the ⚙️ icon to set your OpenAI API key")
    
    # Run the app with the specified host and port
    app.run(host=host, port=port, debug=debug_mode)
