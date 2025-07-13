import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import openai
import json

app = Flask(__name__)
CORS(app)

openai.api_key = os.getenv("OPEN_AI_KEY")

MEMORY_FILE = "felix_user_memory.json"

# Load or initialize memory
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
    data = request.get_json()
    user_input = data.get("message", "").strip()
    user_ip = request.remote_addr

    # Initialize user memory
    if user_ip not in user_data:
        user_data[user_ip] = {"name": None}
    user_mem = user_data[user_ip]

    # Special reset command
    if user_input == "CrimsonResetConfigData":
        user_mem["name"] = None
        save_memory()
        return jsonify({"reply": "Memory reset. I forgot your name. Please tell me again! (^_^)"})

    # Store name if given
    if user_input.lower().startswith("my name is"):
        name = user_input[11:].strip().title()
        user_mem["name"] = name
        save_memory()
        return jsonify({"reply": f"Oh, nice to meet you, {name}! (^_^)"}), 200

    try:
        # Let Felix answer anything, even if name not given
        messages = [
            {"role": "system", "content": "You are Felix, a cute and helpful AI assistant who speaks kindly and with emojis."},
            {"role": "user", "content": user_input}
        ]
        chat_response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",  # ✅ More reliable
            messages=messages
        )
        gpt_reply = chat_response["choices"][0]["message"]["content"].strip()

        # If name not known, remind user nicely
        if not user_mem["name"]:
            reply = f"{gpt_reply} ✨ Hi! What’s your name? Please tell me by saying 'My name is ...' (^_^)"
        else:
            reply = f"{gpt_reply} 💬"

        return jsonify({"reply": reply}), 200

    except Exception as e:
        # Print to console for debugging
        print("❌ ERROR:", e)
        return jsonify({"reply": f"Oops! Something went wrong: {str(e)} 😵"}), 500

if __name__ == "__main__":
    app.run(debug=True)
