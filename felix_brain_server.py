import os
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
import openai

app = Flask(__name__)
CORS(app)  # Allow cross-origin requests if needed

openai.api_key = os.getenv("OPEN_AI_KEY")

MEMORY_FILE = "memory.json"
memory = {}

# Load memory from file if exists
def load_memory():
    global memory
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r") as f:
            memory = json.load(f)
    else:
        memory = {}

def save_memory():
    with open(MEMORY_FILE, "w") as f:
        json.dump(memory, f, indent=2)

load_memory()

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json(force=True)
    user_ip = request.remote_addr

    user_message = data.get("message", "").strip()
    password = data.get("password", "")
    user_name = data.get("name", "").strip().title()  # New optional field

    # Initialize user memory if needed
    user_mem = memory.get(user_ip, {"name": "", "chat_history": []})

    # If user name not set yet, check if client sent it now
    if not user_mem["name"]:
        if user_name:
            user_mem["name"] = user_name
            memory[user_ip] = user_mem
            save_memory()
            return jsonify({"reply": f"Nice to meet you, {user_mem['name']}! (^_^)"})
        else:
            return jsonify({"reply": "Hello! I don't know your name yet. Please send your name with your message like {\"message\": \"hi\", \"name\": \"YourName\"}."})

    # Here you can add a password check if you want to allow memory edits:
    if password != "your_secret_password":
        # Password wrong or not given, disallow memory editing or commands that need password
        pass

    # Add user message to chat history
    user_mem["chat_history"].append({"role": "user", "content": user_message})

    # Limit chat history length to prevent huge context
    if len(user_mem["chat_history"]) > 20:
        user_mem["chat_history"] = user_mem["chat_history"][-20:]

    # Prepare messages for OpenAI API
    messages = [{"role": "system", "content": "You are Felix, a friendly chatbot."}] + user_mem["chat_history"]

    try:
        # Call OpenAI ChatCompletion API
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.7,
        )
        reply = response.choices[0].message.content.strip()

        # Append assistant reply to chat history
        user_mem["chat_history"].append({"role": "assistant", "content": reply})

        # Save updated memory
        memory[user_ip] = user_mem
        save_memory()

        return jsonify({"reply": reply})

    except Exception as e:
        print("OpenAI API error:", e)
        return jsonify({"reply": "Sorry, I am having trouble responding right now. Please try again later."}), 500


if __name__ == "__main__":
    port = int(os.getenv("PORT", 6969))
    app.run(host="0.0.0.0", port=port)
