import os
import string
import datetime
import re
import math
import json
from flask import Flask, request, jsonify, render_template, send_from_directory
import google.generativeai as genai

# Load environment variables from .env file if it exists
try:
    from dotenv import load_dotenv
    load_dotenv()  # take environment variables from .env
    print("Loaded environment variables from .env file")
except ImportError:
    print("python-dotenv not installed, using existing environment variables")

# Configure the Gemini API - no need to specify version

# Initialize the Flask app with static folder
app = Flask(__name__, static_folder="static", static_url_path="/static")

# Create a Google Gemini Client - with a fallback to None if no API key is available
try:
    # Try to initialize the Gemini client
    gemini_api_key = os.environ.get("GEMINI_API_KEY")
    if gemini_api_key:
        genai.configure(api_key=gemini_api_key)
        # Test if the configuration works by creating a basic model
        model = genai.GenerativeModel('gemini-pro')
        api_key_set = True
    else:
        model = None
        api_key_set = False
except Exception as e:
    print(f"Gemini client initialization failed: {e}")
    model = None
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
    """Get a response from Google Gemini API."""
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
            
        # If API key is available and model is initialized, use Gemini
        if model and api_key_set:
            try:
                # Using Gemini's generate_content method directly
                system_prompt = "You are a helpful, friendly, and concise assistant. Provide short and direct answers to user questions."
                full_prompt = f"{system_prompt}\n\nUser: {message}"
                
                # Generate content directly
                response = model.generate_content(full_prompt)
                
                # Return the text from the response
                return response.text
            except Exception as e:
                print(f"Error generating content: {e}")
                # Try alternative method if the first one fails
                try:
                    response = model.generate_content(message)
                    return response.text
                except:
                    return "I'm having trouble processing your request with Gemini. Please check your API key and internet connection."
        else:
            # Fallback if no API key is available
            return "To use the AI features, please set your Gemini API key in the settings menu (⚙️). For now, I can only handle basic date, time, and math questions."
    
    except Exception as e:
        print(f"Error with Gemini API: {e}")
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
                        "message": "Set your API key in the settings menu (⚙️) to use the Gemini AI features."})

@app.route('/set_api_key', methods=['POST'])
def set_api_key():
    """Endpoint to set API key (not for production use)"""
    global model, api_key_set
    
    try:
        data = request.get_json()
        api_key = data.get('api_key', '')
        if not api_key:
            return jsonify({"status": "error", "message": "No API key provided"})
        
        # This only sets the key for the current session and is not secure for production
        os.environ["GEMINI_API_KEY"] = api_key
        
        # Update the model with the new key
        try:
            genai.configure(api_key=api_key)
            # Test if the configuration works by creating a basic model
            model = genai.GenerativeModel('gemini-pro')
            # Test with a simple prompt
            model.generate_content("Hello")
            api_key_set = True
            return jsonify({"status": "success", "message": "API key set successfully"})
        except Exception as e:
            print(f"Error setting Gemini API key: {e}")
            os.environ.pop("GEMINI_API_KEY", None)
            api_key_set = False
            return jsonify({"status": "error", "message": f"Invalid API key or Gemini API error: {str(e)}"})
            
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
    print(f"Gemini API Key {'is' if api_key_set else 'is NOT'} configured.")
    print(f"Server running at http://{host}:{port}/ (locally: http://127.0.0.1:{port}/)")
    print("Click the ⚙️ icon to set your Gemini API key")
    
    # Run the app with the specified host and port
    app.run(host=host, port=port, debug=debug_mode)
