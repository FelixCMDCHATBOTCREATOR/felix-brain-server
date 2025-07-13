import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI
import json

app = Flask(__name__)
CORS(app)

# Initialize OpenAI client with environment key
client = OpenAI(api_key=os.getenv("OPEN_AI_KEY"))

# Memory file for user data
MEMORY_FILE = "felix_user_memory.json"

# Load or initialize user memory
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

    if not user_input:
        return jsonify({"reply": "No input received 😵"}), 400

    # Reset command from client
    if "CrimsonResetConfigData" in user_input:
        if user_ip in user_data:
            user_data[user_ip]["name"] = None
            save_memory()
        return jsonify({"reply": "Memory reset. Please tell me your name again. (^_^)"})

    if user_ip not in user_data:
        user_data[user_ip] = {"name": None}

    user_mem = user_data[user_ip]

    # Name set logic
    if user_input.lower().startswith("my name is"):
        name = user_input[11:].strip().title()
        user_mem["name"] = name
        save_memory()
        return jsonify({"reply": f"Oh, nice to meet you, {name}! (^_^)"}), 200

    try:
        # Use ChatGPT to get response
        response = client.chat.completions.create(
            model="gpt-4",  # or "gpt-3.5-turbo"
            messages=[
                {"role": "system", "content": "You are Felix, a friendly, emoji-using assistant who replies cutely."},
                {"role": "user", "content": user_input}
            ]
        )
        gpt_reply = response.choices[0].message.content.strip()

        # Add name reminder if name not known
        if not user_mem["name"]:
            reply = f"{gpt_reply} ✨ Hi! What’s your name? Please tell me by saying 'My name is ...' (^_^)"
        else:
            reply = f"{gpt_reply} 💬"

        return jsonify({"reply": reply}), 200

    except Exception as e:
        return jsonify({"reply": f"❌ ERROR contacting OpenAI: {e}"}), 500

if __name__ == "__main__":
    app.run(debug=True)
