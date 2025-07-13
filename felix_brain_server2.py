import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import openai
import json

app = Flask(__name__)
CORS(app)

# Load OpenAI key from environment variable
openai.api_key = os.getenv("OPEN_AI_KEY")

MEMORY_FILE = "felix_user_memory.json"

# Load memory from file
if os.path.exists(MEMORY_FILE):
    with open(MEMORY_FILE, "r") as f:
        user_data = json.load(f)
else:
    user_data = {}

# Save memory to file
def save_memory():
    with open(MEMORY_FILE, "w") as f:
        json.dump(user_data, f)

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    user_input = data.get("message", "").strip()
    user_ip = request.remote_addr

    # Create memory entry if missing
    if user_ip not in user_data:
        user_data[user_ip] = {"name": None}

    user_mem = user_data[user_ip]

    # RESET command
    if user_input == "CrimsonResetConfigData":
        user_mem["name"] = None
        save_memory()
        return jsonify({"reply": "Okay! I forgot your name. Please tell me again using 'My name is ...' (^_^)"})

    # If user introduces their name
    if user_input.lower().startswith("my name is"):
        name = user_input[11:].strip().title()
        user_mem["name"] = name
        save_memory()
        return jsonify({"reply": f"Oh, nice to meet you, {name}! (^_^)"}), 200

    try:
        # ChatGPT call
        messages = [
            {
                "role": "system",
                "content": "You are Felix, a cute and helpful AI assistant who always replies kindly, uses emojis, and speaks in a friendly tone like a digital pet named Felix."
            },
            {"role": "user", "content": user_input}
        ]

        chat_response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=messages
        )

        gpt_reply = chat_response["choices"][0]["message"]["content"].strip()

        # Add name prompt only if name is missing
        if not user_mem["name"]:
            reply = f"{gpt_reply} ✨ By the way, what’s your name? Say 'My name is ...' so I can remember you! (^_^)"
        else:
            reply = f"{gpt_reply} 💬"

        return jsonify({"reply": reply}), 200

    except Exception as e:
        return jsonify({"reply": f"Oops! Something went wrong on my side 😵: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(debug=True)
