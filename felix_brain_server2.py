import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import openai
import json
import traceback

app = Flask(__name__)
CORS(app)

# Load OpenAI API key from environment
openai.api_key = os.getenv("OPEN_AI_KEY")

# Memory file to store per-user data
MEMORY_FILE = "felix_user_memory.json"

# Load or create user memory
if os.path.exists(MEMORY_FILE):
    with open(MEMORY_FILE, "r") as f:
        user_data = json.load(f)
else:
    user_data = {}

def save_memory():
    with open(MEMORY_FILE, "w") as f:
        json.dump(user_data, f)

@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json()
        user_input = data.get("message", "").strip()
        user_ip = request.remote_addr or "unknown"
        password = data.get("password", "")

        if not user_input:
            return jsonify({"reply": "Felix didn’t receive anything to answer! 😅"}), 400

        # Reset name if command is sent
        if user_input == "CrimsonResetConfigData":
            if user_ip in user_data:
                user_data[user_ip]["name"] = None
                save_memory()
                return jsonify({"reply": "Okay! I forgot your name. Please tell me again. (^_^)"}), 200

        # Make sure user has an entry
        if user_ip not in user_data:
            user_data[user_ip] = {"name": None}

        user_mem = user_data[user_ip]

        # Name capture
        if user_input.lower().startswith("my name is"):
            name = user_input[11:].strip().title()
            user_mem["name"] = name
            save_memory()
            return jsonify({"reply": f"Yay! Nice to meet you, {name}! What can I do for you? (^_^)"}), 200

        # Prepare prompt for ChatGPT
        messages = [
            {
                "role": "system",
                "content": (
                    "You are Felix, a cute, helpful assistant who replies with emojis, personality, kindness, and fun facts. "
                    "Your creator is Crimson. Never ask for name unless you don't know it. No long intros, no 'here's what I found'. "
                    "Always act like Felix in every message."
                )
            },
            {"role": "user", "content": user_input}
        ]

        chat_response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=messages,
            temperature=0.7,
            max_tokens=300
        )

        gpt_reply = chat_response.choices[0].message.content.strip()

        if not user_mem["name"]:
            reply = f"{gpt_reply} ✨ By the way, what’s your name? Say 'My name is ...' so I can remember you! (^_^)"
        else:
            reply = f"{gpt_reply} 💬"

        return jsonify({"reply": reply}), 200

    except Exception as e:
        # Log traceback to server logs (will show on Render)
        print("❌ Server error:\n", traceback.format_exc())
        return jsonify({"reply": "Felix got a brain-freeze while thinking 🧠❄️"}), 500

if __name__ == "__main__":
    app.run(debug=True)
