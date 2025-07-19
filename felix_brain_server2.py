import os
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

app = Flask(__name__)
CORS(app)

client = OpenAI(api_key=os.getenv("OPEN_AI_KEY"))

# Files
MEMORY_FILE = "felix_user_memory.json"
LOG_FILE = "server_log.txt"
USER_REGISTRY_FILE = "user_registry.txt"

# Load user memory
if os.path.exists(MEMORY_FILE):
    with open(MEMORY_FILE, "r", encoding="utf-8") as f:
        user_data = json.load(f)
else:
    user_data = {}

def log_event(text):
    timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"{timestamp} {text}\n")

def log_user_registry(ip, name, uid):
    if not os.path.exists(USER_REGISTRY_FILE):
        with open(USER_REGISTRY_FILE, "w", encoding="utf-8") as f:
            f.write("=== Felix User Registry ===\n")

    entry = f"{ip} | ID {uid} | {name}"
    with open(USER_REGISTRY_FILE, "r", encoding="utf-8") as f:
        if entry in f.read():
            return  # Already logged

    timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    with open(USER_REGISTRY_FILE, "a", encoding="utf-8") as f:
        f.write(f"{timestamp} {entry}\n")

def save_memory():
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(user_data, f, ensure_ascii=False, indent=2)

def get_next_id():
    ids = [info.get("id", 0) for info in user_data.values()]
    return max(ids, default=0) + 1

@app.route("/")
def home():
    return "Felix Brain Server is running."

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json(force=True)
    user_input = data.get("message", "").strip()
    user_ip = request.remote_addr or "unknown"

    if not user_input:
        return jsonify({"reply": "No input received 😵"}), 400

    if "CrimsonResetConfigData" in user_input:
        if user_ip in user_data:
            old_name = user_data[user_ip].get("name", "Unknown")
            old_id = user_data[user_ip].get("id", "?")
            user_data[user_ip] = {"name": None, "id": old_id}
            save_memory()
            log_event(f"♻️ <{old_name} #{old_id}> reset their memory.")
        return jsonify({"reply": "Memory reset. Please tell me your name again. (^_^)"}), 200

    if user_ip not in user_data:
        user_data[user_ip] = {"name": None, "id": get_next_id()}
        save_memory()

    user_mem = user_data[user_ip]
    user_id = user_mem["id"]
    user_name = user_mem["name"]

    if user_input.lower().startswith("my name is"):
        name = user_input[11:].strip().title()
        if not user_name:
            user_mem["name"] = name
            save_memory()
            log_user_registry(user_ip, name, user_id)
            log_event(f"📝 <{user_ip}> set name to: {name} (ID #{user_id})")
            return jsonify({"reply": f"Oh, nice to meet you, {name}! You’re user #{user_id} (^_^)"}), 200
        else:
            return jsonify({"reply": f"You already set your name as {user_name} (User #{user_id})"}), 200

    if not user_name:
        return jsonify({"reply": "👀 Please tell me your name first by saying 'My name is ...' (^_^)"}), 200

    try:
        log_event(f"📨 <{user_name} #{user_id}> said: {user_input}")

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": f"You are Felix, a cute chatbot. The user's name is {user_name}."},
                {"role": "user", "content": user_input}
            ]
        )

        reply = response.choices[0].message.content.strip()
        log_event(f"🤖 Felix replied: {reply}")
        return jsonify({"reply": f"{reply} 💬"}), 200

    except Exception as e:
        error_msg = f"❌ ERROR from OpenAI: {e}"
        log_event(error_msg)
        return jsonify({"reply": error_msg}), 500

if __name__ == "__main__":
    log_event("🚀 Server starting...")
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
