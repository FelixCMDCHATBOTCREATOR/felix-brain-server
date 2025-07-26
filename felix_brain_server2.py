import os, json, logging, re, random
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from datetime import datetime
from tinydb import TinyDB, Query
import openai

# Setup
load_dotenv()
app = Flask(__name__)
CORS(app)
openai.api_key = os.getenv("OPEN_AI_KEY")

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Felix")

# Memory DB
db = TinyDB("user_memory.json")
User = Query()

# Game list
GAMES = [
    "Arsenal", "Doors", "Brookhaven", "Blox Fruits", "Adopt Me",
    "Natural Disaster Survival", "Tower of Hell", "Murder Mystery 2",
    "Jailbreak", "BedWars", "Piggy", "Phantom Forces", "Evade"
]

# Joke list
JOKES = [
    "Why did the computer get cold? Because it left its Windows open!",
    "Why don’t robots ever get scared? They have nerves of steel!",
    "What do you get when you cross a chatbot with a joke? Me!",
    "I would tell you a UDP joke, but you might not get it.",
    "Why was the JavaScript developer sad? Because he didn’t know how to ‘null’ his feelings."
]

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

def matches(text, words):
    return any(word in text.lower() for word in words)

@app.route("/")
def home():
    return jsonify({
        "status": "Felix Brain Server is running",
        "version": "2.5",
        "openai_status": "connected",
        "endpoints": ["/", "/chat", "/health", "/ask"]
    })

@app.route("/health")
def health():
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    })

@app.route("/ask", methods=["POST"])
@app.route("/chat", methods=["POST"])
def chat():
    try:
        user_ip = request.headers.get('X-Forwarded-For', request.remote_addr or "unknown").split(',')[0].strip()
        data = request.get_json(force=True)
        user_input = data.get("message", "").strip().lower()

        if not user_input:
            return jsonify({"reply": "No input received 😵", "status": "error"}), 400

        if "crimsonresetconfigdata" in user_input:
            db.remove(User.ip == user_ip)
            return jsonify({"reply": "🧼 Memory reset. Please say 'My name is ...' to begin again!", "status": "success"}), 200

        user = get_or_create_user(user_ip)
        user_id = user["id"]
        user_name = user["name"]

        name = extract_name(user_input)
        if name:
            if not user_name:
                update_user(user_ip, "name", name)
                return jsonify({"reply": f"Welcome, {name}! You're user #{user_id} 🎉", "status": "success"}), 200
            else:
                return jsonify({"reply": f"You're already logged in as {user_name} (# {user_id}) 👋", "status": "info"}), 200

        if not user_name:
            return jsonify({"reply": "👀 Tell me your name first by saying 'My name is ...'", "status": "info"}), 200

        # Help command
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

        # Music
        if "musicplay" in user_input:
            return jsonify({"reply": "🎵 Opening YouTube Music! Type the song name next or say 'open music website'.", "status": "success"}), 200

        # Games
        if "what games can you play" in user_input:
            return jsonify({"reply": f"🎮 I can play these Roblox games: {', '.join(GAMES)}", "status": "success"}), 200

        if "play " in user_input:
            for game in GAMES:
                if game.lower() in user_input:
                    return jsonify({"reply": f"🕹️ Launching {game} now... (or simulating it!)", "status": "success"}), 200
            return jsonify({"reply": "❌ Sorry, I don't know that game. Try saying 'what games can you play'!", "status": "info"}), 200

        # Joke
        if "joke" in user_input:
            return jsonify({"reply": f"😂 {random.choice(JOKES)}", "status": "success"}), 200

        # GPT Fallback
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": f"You are Felix, a fun and friendly chatbot. The user's name is {user_name}. Always be helpful, creative, and cheerful."},
                {"role": "user", "content": user_input}
            ],
            temperature=0.7,
            max_tokens=200
        )

        reply = response.choices[0].message.content.strip()
        return jsonify({"reply": f"{reply} 💬", "status": "success"}), 200

    except openai.error.AuthenticationError:
        logger.error("❌ Invalid OpenAI API key")
        return jsonify({"reply": "Authentication error. Please check your API key 🔑", "status": "error"}), 500
    except Exception as e:
        logger.error(f"❌ Chat error: {e}")
        return jsonify({"reply": "Oops, something broke 😵 Try again!", "status": "error"}), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found", "status": "error"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error", "status": "error"}), 500

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    logger.info(f"🚀 Felix Brain running on port {port} | Debug: {debug}")
    app.run(host="0.0.0.0", port=port, debug=debug)
