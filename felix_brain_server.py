from flask import Flask, request, jsonify
import json
import openai
import os

app = Flask(__name__)
openai.api_key = os.getenv("OPEN_AI_KEY", "")  # Use environment variable for your key

MEMORY_FILE = "felix_memory.json"
EDIT_PASSWORD = "jayeshhagucaihahah"

if os.path.exists(MEMORY_FILE):
    with open(MEMORY_FILE, "r", encoding="utf-8") as f:
        memory = json.load(f)
else:
    memory = {"name": None, "favorite_color": None, "favorite_game": None}

def save_memory():
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(memory, f, indent=4)

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    user_message = data.get("message", "").lower()
    password = data.get("password", "")

    if user_message.startswith("my name is "):
        if password != EDIT_PASSWORD:
            return jsonify({"reply": "⛔ Wrong password for changing name!"})
        memory["name"] = user_message[11:].strip().title()
        save_memory()
        return jsonify({"reply": f"Nice to meet you, {memory['name']}! (^_^)"} )

    if user_message.startswith("my favorite color is "):
        if password != EDIT_PASSWORD:
            return jsonify({"reply": "⛔ Wrong password for changing color!"})
        memory["favorite_color"] = user_message[21:].strip().title()
        save_memory()
        return jsonify({"reply": f"{memory['favorite_color']} is awesome! (^_^)"})

    if user_message.startswith("my favorite game is "):
        if password != EDIT_PASSWORD:
            return jsonify({"reply": "⛔ Wrong password for changing game!"})
        memory["favorite_game"] = user_message[20:].strip().title()
        save_memory()
        return jsonify({"reply": f"I’ll remember {memory['favorite_game']}! (^_^)"})

    if "what is my name" in user_message:
        return jsonify({"reply": f"You're {memory['name']}!" if memory["name"] else "I don't know your name yet."})

    if "what is my favorite color" in user_message:
        return jsonify({"reply": f"Your favorite color is {memory['favorite_color']}!" if memory["favorite_color"] else "I don't know your color yet."})

    if "what is my favorite game" in user_message:
        return jsonify({"reply": f"Your favorite game is {memory['favorite_game']}!" if memory["favorite_game"] else "Tell me your favorite game first!"})

    if "joke" in user_message:
        return jsonify({"reply": "Why was the computer cold? Because it left its Windows open! 😹 (^_^)"})

    try:
        response = openai.ChatCompletion.create(
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
