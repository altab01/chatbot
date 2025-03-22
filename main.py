import os
import string
import datetime
import re
import math
import json
from flask import Flask, request, jsonify, render_template, send_from_directory
import google.generativeai as genai
from sqlalchemy import text
from models import db, ChatMessage

# Load environment variables from .env file if it exists
try:
    from dotenv import load_dotenv
    load_dotenv()  # take environment variables from .env
    print("Loaded environment variables from .env file")
except ImportError:
    print("python-dotenv not installed, using existing environment variables")

# Initialize the Flask app with static folder
app = Flask(__name__, static_folder="static", static_url_path="/static")

# Configure database
database_url = os.environ.get("DATABASE_URL")
if database_url:
    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    # Add database connection pooling settings to handle connection issues
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_recycle": 280,
        "pool_timeout": 20,
        "pool_pre_ping": True,
        "max_overflow": 5
    }
    db.init_app(app)
    
    # Create database tables
    with app.app_context():
        try:
            db.create_all()
            print("Database tables created successfully")
        except Exception as db_error:
            print(f"Database initialization error: {db_error}")
            print("The application will continue running but database features may be limited")
else:
    print("WARNING: DATABASE_URL not found in environment variables!")

# Create a Google Gemini Client - with a fallback to None if no API key is available
try:
    # Try to initialize the Gemini client
    gemini_api_key = os.environ.get("GEMINI_API_KEY")
    if gemini_api_key:
        genai.configure(api_key=gemini_api_key)
        # Try to retrieve available models
        try:
            # Convert generator to list
            available_models_list = list(genai.list_models())
            model_names = [m.name for m in available_models_list]
            print("Available Gemini models:", model_names)
            
            # Try to find an appropriate Gemini model
            model_name = 'models/gemini-1.5-pro'  # Default
            
            # Find the best model
            if any('gemini-1.5-pro' in m for m in model_names):
                for m in model_names:
                    if 'gemini-1.5-pro' in m and 'vision' not in m:
                        model_name = m
                        break
            elif any('gemini-2.0-pro' in m for m in model_names):
                for m in model_names:
                    if 'gemini-2.0-pro' in m:
                        model_name = m
                        break
            elif any('gemini' in m for m in model_names):
                for m in model_names:
                    if 'gemini' in m and 'vision' not in m:
                        model_name = m
                        break
            elif any('text' in m for m in model_names):
                for m in model_names:
                    if 'text' in m:
                        model_name = m
                        break
            elif model_names:
                model_name = model_names[0]
            
            print(f"Using model: {model_name}")
            model = genai.GenerativeModel(model_name)
            api_key_set = True
        except Exception as e:
            print(f"Error listing models: {e}")
            # Fallback to a standard model
            model = genai.GenerativeModel('models/gemini-1.5-pro')
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
        
        # Save the chat message to the database
        # Only attempt to save if database is configured
        database_url = os.environ.get("DATABASE_URL")
        if database_url:
            try:
                chat_message = ChatMessage(
                    user_message=message,
                    bot_response=response
                )
                db.session.add(chat_message)
                db.session.commit()
                print(f"Chat message saved to database with ID: {chat_message.id}")
            except Exception as db_error:
                print(f"Error saving to database: {db_error}")
                # Try to handle database errors gracefully
                try:
                    db.session.rollback()
                except:
                    pass  # Ignore if rollback also fails
                # Continue with response even if database save fails
        else:
            print("Database not configured - not saving chat history")
        
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

@app.route('/get_chat_history', methods=['GET'])
def get_chat_history():
    """Endpoint to retrieve chat history from the database"""
    try:
        # Check if database is configured
        database_url = os.environ.get("DATABASE_URL")
        if not database_url:
            return jsonify({"status": "error", "message": "Database not configured"})
        
        try:
            # Fetch chat history from the database
            # Get latest 50 messages, ordered by timestamp (newest first)
            # Note: We're already in an app context from the route
            
            # Ensure a fresh connection
            db.session.remove()
            
            # Get the chat messages - directly try to query without ping test
            chat_messages = ChatMessage.query.order_by(ChatMessage.timestamp.desc()).limit(50).all()
            
            # Convert to list of dictionaries for JSON response
            history = [message.to_dict() for message in chat_messages]
            
            return jsonify({"status": "success", "history": history})
        except Exception as db_error:
            print(f"Database query error: {db_error}")
            
            # Attempt to recover the connection
            try:
                db.session.rollback()
                db.session.remove()
            except:
                pass
                
            # Return a user-friendly error message
            return jsonify({
                "status": "error", 
                "message": "Unable to retrieve chat history. The database connection may be temporarily unavailable.",
                "history": []  # Return an empty history so the app can still function
            })
    except Exception as e:
        print(f"Error retrieving chat history: {e}")
        return jsonify({
            "status": "error", 
            "message": "Error retrieving chat history", 
            "history": []  # Return an empty history so the app can still function
        })

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
            # Try to retrieve available models first
            try:
                # Convert generator to list
                available_models_list = list(genai.list_models())
                model_names = [m.name for m in available_models_list]
                print("Set API Key - Available Gemini models:", model_names)
                
                # Try to find an appropriate Gemini model
                model_name = 'models/gemini-1.5-pro'  # Default
                
                # Find the best model
                if any('gemini-1.5-pro' in m for m in model_names):
                    for m in model_names:
                        if 'gemini-1.5-pro' in m and 'vision' not in m:
                            model_name = m
                            break
                elif any('gemini-2.0-pro' in m for m in model_names):
                    for m in model_names:
                        if 'gemini-2.0-pro' in m:
                            model_name = m
                            break
                elif any('gemini' in m for m in model_names):
                    for m in model_names:
                        if 'gemini' in m and 'vision' not in m:
                            model_name = m
                            break
                elif any('text' in m for m in model_names):
                    for m in model_names:
                        if 'text' in m:
                            model_name = m
                            break
                elif model_names:
                    model_name = model_names[0]
                        
                print(f"Using model: {model_name}")
                model = genai.GenerativeModel(model_name)
                
                # Test with a simple prompt
                response = model.generate_content("Hello")
                if response and hasattr(response, 'text'):
                    api_key_set = True
                else:
                    raise Exception("No valid response from model")
            except Exception as model_error:
                print(f"Error with models list: {model_error}. Trying with default model.")
                # Fallback to default model
                model = genai.GenerativeModel('models/gemini-1.5-pro')
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
