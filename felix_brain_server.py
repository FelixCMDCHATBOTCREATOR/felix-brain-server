from flask import Flask, request, jsonify
import json
import os
from openai import OpenAI
from datetime import datetime

app = Flask(__name__)
OPENAI_KEY = os.getenv("OPEN_AI_KEY", "")
client = OpenAI(api_key=OPENAI_KEY)

MEMORY_FILE = "felix_memory.json"
EDIT_PASSWORD = "jayeshhagucaihahah"

if os.path.exists(MEMORY_FILE):
    with open(MEMORY_FILE, "r", encoding="utf-8") as f:
        memory = json.load(f)
else:
    memory = {}

def save_memory():
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(memory, f, indent=4)

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    user_message = data.get("message", "").lower()
    password = data.get("password", "")
    user_ip = request.remote_addr

    # Create per-user memory
    user_mem = memory.get(user_ip, {"name": None, "favorite_color": None, "favorite_game": None})

    # Logging every message
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {user_ip} says: {user_message}")

    # First time: ask for name
    if user_mem["name"] is None:
        memory[user_ip] = user_mem
        save_memory()
        return jsonify({"reply": "Hi there! What’s your name? Please type: my name is <your name>"})

    # Memory updates
    if user_message.startswith("my name is "):
        if password != EDIT_PASSWORD:
            return jsonify({"reply": "⛔ Wrong password for changing name!"})
        user_mem["name"] = user_message[11:].strip().title()

    elif user_message.startswith("my favorite color is "):
        if password != EDIT_PASSWORD:
            return jsonify({"reply": "⛔ Wrong password for changing color!"})
        user_mem["favorite_color"] = user_message[21:].strip().title()

    elif user_message.startswith("my favorite game is "):
        if password != EDIT_PASSWORD:
            return jsonify({"reply": "⛔ Wrong password for changing game!"})
        user_mem["favorite_game"] = user_message[20:].strip().title()

    # Save updates
    memory[user_ip] = user_mem
    save_memory()

    # Predefined questions
    if "what is my name" in user_message:
        return jsonify({"reply": f"You're {user_mem['name']}!"})

    if "what is my favorite color" in user_message:
        return jsonify({"reply": f"Your favorite color is {user_mem['favorite_color']}!" if user_mem["favorite_color"] else "I don't know your favorite color yet."})

    if "what is my favorite game" in user_message:
        return jsonify({"reply": f"Your favorite game is {user_mem['favorite_game']}!" if user_mem["favorite_game"] else "Tell me your favorite game first!"})

    if "joke" in user_message:
        return jsonify({"reply": "Why was the computer cold? Because it left its Windows open! 😹 (^_^)"})

    # GPT response fallback
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": user_message}]
        )
        gpt_reply = response.choices[0].message.content.strip()
        return jsonify({"reply": gpt_reply})
    except Exception as e:
        return jsonify({"reply": f"Sorry, GPT failed: {e}"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 6969))
    app.run(host="0.0.0.0", port=port)
