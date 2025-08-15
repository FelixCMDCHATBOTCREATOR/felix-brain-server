import os
import json
import logging
import re
import random
from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI
from dotenv import load_dotenv
from datetime import datetime
from tinydb import TinyDB, Query

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app, origins="*")  # Allow all origins for testing

# Initialize OpenAI client
api_key = os.getenv("OPEN_AI_KEY") or os.getenv("OPENAI_API_KEY")
if not api_key:
    raise RuntimeError("❌ No OpenAI API key found in environment variables.")

try:
    client = OpenAI(api_key=api_key)
    logger.info("✅ OpenAI client initialized successfully.")
    # Optional test request
    test_response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": "Hi"}],
        max_tokens=5
    )
    logger.info("✅ OpenAI API test successful - Felix brain is connected!")
except Exception as e:
    logger.error(f"❌ OpenAI initialization failed: {e}")
    client = None

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MEMORY_FILE = os.path.join(BASE_DIR, "felix_user_memory.json")
LOG_FILE = os.path.join(BASE_DIR, "server_log.txt")
USER_REGISTRY_FILE = os.path.join(BASE_DIR, "user_registry.txt")

# Load user memory
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

# Helper functions
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
        if os.path.exists(USER_REGISTRY_FILE):
            with open(USER_REGISTRY_FILE, "r", encoding="utf-8") as f:
                if entry in f.read():
                    return
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

# TinyDB setup
db = TinyDB("user_memory.json")
User = Query()

# Supported games & jokes
GAMES = [
    "Arsenal", "Doors", "Brookhaven", "Blox Fruits", "Adopt Me",
    "Natural Disaster Survival", "Tower of Hell", "Murder Mystery 2",
    "Jailbreak", "BedWars", "Piggy", "Phantom Forces", "Evade"
]

JOKES = [
    "Why did the computer get cold? Because it left its Windows open!",
    "Why don’t robots ever get scared? They have nerves of steel!",
    "What do you get when you cross a chatbot with a joke? Me!",
    "I would tell you a UDP joke, but you might not get it.",
    "Why was the JavaScript developer sad? Because he didn’t know how to ‘null’ his feelings."
]

# User helpers
def get_or_create_user(ip):
    user = db.get(User.ip == ip)
    if not user:
        user = {"ip": ip, "name": None, "id": len(db) + 1}
        db.insert(user)
    return user

def update_user(ip, field, value):
    db.update({field: value}, User.ip == ip)

def extract_name(text):
    match = re.search(r"(?:my name is|i'?m|this is)\s+([A-Za-z]+)", text, re.I)
    return match.group(1).title() if match else None

# Routes
@app.route("/")
def home():
    return jsonify({
        "status": "Felix Brain Server is running",
        "version": "2.5",
        "openai_status": "connected" if client else "disconnected",
        "endpoints": ["/", "/chat", "/health", "/ask"]
    })

@app.route("/health")
def health():
    return jsonify({
        "status": "healthy",
        "openai_connected": client is not None,
        "timestamp": datetime.now().isoformat()
    }), 200

@app.route("/ask", methods=["POST"])
@app.route("/chat", methods=["POST"])
def chat():
    try:
        # Get user IP
        user_ip = request.headers.get('X-Forwarded-For', request.remote_addr or "unknown").split(',')[0].strip()
        logger.info(f"Chat request from IP: {user_ip}")

        data = request.get_json(force=True)
        user_input = data.get("message", "").strip().lower()
        if not user_input:
            return jsonify({"reply": "No input received 😵", "status": "error"}), 400

        # Reset commands
        if "crimsonresetconfigdata" in user_input:
            if user_ip in user_data:
                user_mem = user_data[user_ip]
                user_mem["name"] = None
                save_memory()
            db.remove(User.ip == user_ip)
            return jsonify({"reply": "🧼 Memory reset. Please say 'My name is ...' to begin again!", "status": "success"}), 200

        # Initialize user if new
        if user_ip not in user_data:
            user_data[user_ip] = {"name": None, "id": get_next_id()}
            save_memory()
        user = get_or_create_user(user_ip)
        user_mem = user_data[user_ip]
        user_id = user_mem["id"]
        user_name = user_mem["name"]

        # Name handling
        name = extract_name(user_input)
        if name and not user_name:
            user_mem["name"] = name
            save_memory()
            log_user_registry(user_ip, name, user_id)
            log_event(f"📝 <{user_ip}> set name to: {name} (ID #{user_id})")
            return jsonify({"reply": f"Oh, nice to meet you, {name}! You're user #{user_id} (^_^)", "status": "success"}), 200

        if not user_name:
            return jsonify({"reply": "👀 Please tell me your name first by saying 'My name is ...' (^_^)", "status": "info"}), 200

        # Check OpenAI client
        if client is None:
            return jsonify({"reply": "Sorry, I'm having trouble connecting to my brain right now 😅 Check the API key!", "status": "error"}), 500

        log_event(f"📨 <{user_name} #{user_id}> said: {user_input}")

        # Commands
        if "help" in user_input:
            return jsonify({"reply": (
                "🆘 Felix Help Menu:\n"
                "- Say 'play [game name]' to launch a Roblox game\n"
                "- Say 'musicplay' to listen to music\n"
                "- Ask me anything, I answer over 200+ topics\n"
                "- Say 'tell me a joke' for a funny moment\n"
                "- Type 'CrimsonResetConfigData' to reset your memory\n"
                "- Say 'what games can you play' to see supported games\n"
                "- Or just chat with me like a buddy! 💬"
            ), "status": "success"}), 200

        if "musicplay" in user_input:
            return jsonify({"reply": "🎵 Opening YouTube Music! Type the song name next or say 'open music website'.", "status": "success"}), 200

        if "what games can you play" in user_input:
            return jsonify({"reply": f"🎮 I can play these Roblox games: {', '.join(GAMES)}", "status": "success"}), 200

        if "play " in user_input:
            for game in GAMES:
                if game.lower() in user_input:
                    return jsonify({"reply": f"🕹️ Launching {game} now... (or simulating it!)", "status": "success"}), 200
            return jsonify({"reply": "❌ Sorry, I don't know that game. Try saying 'what games can you play'!", "status": "info"}), 200

        if "joke" in user_input:
            return jsonify({"reply": f"😂 {random.choice(JOKES)}", "status": "success"}), 200

        # OpenAI Chat
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": f"You are Felix, a fun and friendly chatbot. The user's name is {user_name}. Always be helpful, creative, and cheerful."},
                {"role": "user", "content": user_input}
            ],
            temperature=0.7,
            max_tokens=200
        )
        reply = response.choices[0].message.content.strip()
        log_event(f"🤖 Felix replied: {reply}")
        return jsonify({"reply": f"{reply} 💬", "status": "success"}), 200

    except Exception as e:
        error_msg = f"❌ GENERAL ERROR: {str(e)}"
        logger.error(error_msg)
        log_event(error_msg)
        return jsonify({"reply": "Sorry, I encountered an error. Please try again! 😅", "status": "error"}), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Internal server error", "status": "error"}), 500

if __name__ == "__main__":
    log_event("🚀 Server starting...")
    port = int(os.environ.get("PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    logger.info(f"🚀 Felix Brain running on port {port} | Debug: {debug}")
    app.run(host="0.0.0.0", port=port, debug=debug)
