import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import openai
import json

app = Flask(__name__)
CORS(app)

# Load OpenAI key from environment
openai.api_key = os.getenv("OPEN_AI_KEY")

# Memory file
MEMORY_FILE = "felix_user_memory.json"

# Load or initialize memory
if os.path.exists(MEMORY_FILE):
    with open(MEMORY_FILE, "r") as f:
        user_data = json.load(f)
else:
    user_data = {}

# Helper to save memory
def save_memory():
    with open(MEMORY_FILE, "w") as f:
        json.dump(user_data, f)

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    user_input = data.get("message", "").strip()
    user_ip = request.remote_addr
    password = data.get("password", "")

    # Initialize user memory
    if user_ip not in user_data:
        user_data[user_ip] = {"name": None}

    user_mem = user_data[user_ip]

    # Name capture logic
    if user_input.lower().startswith("my name is"):
        name = user_input[11:].strip().title()
        user_mem["name"] = name
        save_memory()
        return jsonify({"reply": f"Yay! Nice to meet you, {name}! What can I do for you? (^_^)"}), 200

    try:
        # Get ChatGPT answer first
        messages = [
            {"role": "system", "content": "You are Felix, a cute and helpful AI assistant who talks with kindness, emojis, and Felix-style."},
            {"role": "user", "content": user_input}
        ]
        chat_response = openai.ChatCompletion.create(model="gpt-4", messages=messages)
        gpt_reply = chat_response["choices"][0]["message"]["content"].strip()

        # If name not known, gently ask after replying
        if not user_mem["name"]:
            reply = f"{gpt_reply} ✨ By the way, what’s your name? Say 'My name is ...' so I can remember you! (^_^)"
        else:
            reply = f"{gpt_reply} 💬"

        return jsonify({"reply": reply}), 200

    except Exception as e:
        return jsonify({"reply": f"Oops! Something went wrong: {str(e)} 😵"}), 500

if __name__ == "__main__":
    app.run(debug=True)
