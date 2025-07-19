import os
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI
from dotenv import load_dotenv
from datetime import datetime
import logging

# Configure logging for better debugging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

app = Flask(__name__)
CORS(app, origins="*")  # Allow all origins for testing

# Initialize OpenAI client with minimal approach
client = None
try:
    # Try the most basic initialization first
    client = OpenAI()
    logger.info("OpenAI client initialized with default settings")
    
except Exception as e1:
    logger.error(f"Default OpenAI init failed: {e1}")
    try:
        # Try with explicit API key
        api_key = os.getenv("OPEN_AI_KEY") or os.getenv("OPENAI_API_KEY")
        if api_key:
            client = OpenAI(api_key=api_key)
            logger.info("OpenAI client initialized with explicit API key")
        else:
            logger.error("No API key found in environment variables")
    except Exception as e2:
        logger.error(f"Explicit API key init also failed: {e2}")
        client = None

# Test the client if it was created successfully
if client:
    try:
        test_response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "test"}],
            max_tokens=5
        )
        logger.info("✅ OpenAI API test successful")
    except Exception as e:
        logger.error(f"OpenAI API test failed: {e}")
        client = None

# Files - Use absolute paths to avoid issues
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MEMORY_FILE = os.path.join(BASE_DIR, "felix_user_memory.json")
LOG_FILE = os.path.join(BASE_DIR, "server_log.txt")
USER_REGISTRY_FILE = os.path.join(BASE_DIR, "user_registry.txt")

# Load user memory with error handling
try:
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            user_data = json.load(f)
        logger.info("User memory loaded successfully")
    else:
        user_data = {}
        logger.info("No existing user memory found, starting fresh")
except Exception as e:
    logger.error(f"Error loading user memory: {e}")
    user_data = {}

def log_event(text):
    timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"{timestamp} {text}\n")
        logger.info(f"Logged: {text}")
    except Exception as e:
        logger.error(f"Failed to write to log file: {e}")

def log_user_registry(ip, name, uid):
    try:
        if not os.path.exists(USER_REGISTRY_FILE):
            with open(USER_REGISTRY_FILE, "w", encoding="utf-8") as f:
                f.write("=== Felix User Registry ===\n")

        entry = f"{ip} | ID {uid} | {name}"
        
        # Check if entry already exists
        if os.path.exists(USER_REGISTRY_FILE):
            with open(USER_REGISTRY_FILE, "r", encoding="utf-8") as f:
                if entry in f.read():
                    return  # Already logged

        timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
        with open(USER_REGISTRY_FILE, "a", encoding="utf-8") as f:
            f.write(f"{timestamp} {entry}\n")
    except Exception as e:
        logger.error(f"Failed to log user registry: {e}")

def save_memory():
    try:
        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(user_data, f, ensure_ascii=False, indent=2)
        logger.info("User memory saved successfully")
    except Exception as e:
        logger.error(f"Failed to save user memory: {e}")

def get_next_id():
    try:
        ids = [info.get("id", 0) for info in user_data.values() if isinstance(info, dict)]
        return max(ids, default=0) + 1
    except Exception as e:
        logger.error(f"Error getting next ID: {e}")
        return 1

@app.route("/")
def home():
    logger.info("Home route accessed")
    return jsonify({
        "status": "Felix Brain Server is running",
        "version": "1.0",
        "openai_status": "connected" if client else "disconnected",
        "endpoints": ["/", "/chat", "/health"]
    })

@app.route("/health")
def health():
    """Health check endpoint for Render"""
    return jsonify({
        "status": "healthy",
        "openai_connected": client is not None,
        "timestamp": datetime.now().isoformat()
    }), 200

@app.route("/chat", methods=["POST"])
def chat():
    try:
        # Get client IP with fallback
        user_ip = request.headers.get('X-Forwarded-For', 
                 request.headers.get('X-Real-IP', 
                 request.remote_addr or "unknown"))
        
        # Handle potential comma-separated IPs from proxies
        if ',' in user_ip:
            user_ip = user_ip.split(',')[0].strip()
        
        logger.info(f"Chat request from IP: {user_ip}")
        
        data = request.get_json(force=True)
        user_input = data.get("message", "").strip()

        if not user_input:
            return jsonify({"reply": "No input received 😵", "status": "error"}), 400

        # Handle reset command
        if "CrimsonResetConfigData" in user_input:
            if user_ip in user_data:
                old_name = user_data[user_ip].get("name", "Unknown")
                old_id = user_data[user_ip].get("id", "?")
                user_data[user_ip] = {"name": None, "id": old_id}
                save_memory()
                log_event(f"♻️ <{old_name} #{old_id}> reset their memory.")
            return jsonify({"reply": "Memory reset. Please tell me your name again. (^_^)", "status": "success"}), 200

        # Initialize user if not exists
        if user_ip not in user_data:
            user_data[user_ip] = {"name": None, "id": get_next_id()}
            save_memory()

        user_mem = user_data[user_ip]
        user_id = user_mem["id"]
        user_name = user_mem["name"]

        # Handle name setting
        if user_input.lower().startswith("my name is"):
            name = user_input[11:].strip().title()
            if not user_name:
                user_mem["name"] = name
                save_memory()
                log_user_registry(user_ip, name, user_id)
                log_event(f"📝 <{user_ip}> set name to: {name} (ID #{user_id})")
                return jsonify({"reply": f"Oh, nice to meet you, {name}! You're user #{user_id} (^_^)", "status": "success"}), 200
            else:
                return jsonify({"reply": f"You already set your name as {user_name} (User #{user_id})", "status": "info"}), 200

        # Require name before chatting
        if not user_name:
            return jsonify({"reply": "👀 Please tell me your name first by saying 'My name is ...' (^_^)", "status": "info"}), 200

        # Check if OpenAI client is available
        if client is None:
            return jsonify({"reply": "Sorry, I'm having trouble connecting to my brain right now 😅 Check the API key!", "status": "error"}), 500

        log_event(f"📨 <{user_name} #{user_id}> said: {user_input}")

        # Make OpenAI request with better error handling
        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": f"You are Felix, a cute and friendly chatbot. The user's name is {user_name}. Keep responses concise and add personality."},
                    {"role": "user", "content": user_input}
                ],
                max_tokens=150,
                temperature=0.7
            )

            reply = response.choices[0].message.content.strip()
            log_event(f"🤖 Felix replied: {reply}")
            return jsonify({"reply": f"{reply} 💬", "status": "success"}), 200
            
        except Exception as openai_error:
            logger.error(f"OpenAI API error: {openai_error}")
            log_event(f"❌ OpenAI ERROR: {str(openai_error)}")
            return jsonify({"reply": "Sorry, my brain is having trouble right now. Please try again! 😅", "status": "error"}), 500

    except Exception as e:
        error_msg = f"❌ GENERAL ERROR: {str(e)}"
        logger.error(error_msg)
        log_event(error_msg)
        return jsonify({"reply": "Sorry, I encountered an error. Please try again! 😅", "status": "error"}), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found", "status": "error"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error", "status": "error"}), 500

if __name__ == "__main__":
    log_event("🚀 Server starting...")
    port = int(os.environ.get("PORT", 5000))
    debug_mode = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    
    logger.info(f"Starting server on port {port}")
    logger.info(f"Debug mode: {debug_mode}")
    logger.info(f"OpenAI client status: {'✅ Connected' if client else '❌ Not connected'}")
    
    app.run(host="0.0.0.0", port=port, debug=debug_mode)
