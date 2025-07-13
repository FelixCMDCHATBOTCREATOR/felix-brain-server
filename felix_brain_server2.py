import os
from flask import Flask, request, jsonify
import openai
import threading

app = Flask(__name__)

# Load your OpenAI API key from environment variable
openai.api_key = os.getenv("OPEN_AI_KEY")

# In-memory user memory storage: { ip: { "name": str, "history": [...] } }
user_memories = {}
mem_lock = threading.Lock()

def get_user_memory(ip):
    with mem_lock:
        if ip not in user_memories:
            user_memories[ip] = {"name": None, "history": []}
        return user_memories[ip]

def create_felix_prompt(memory, user_message):
    # Basic conversation context + memory
    system_msg = {
        "role": "system",
        "content": (
            "You are Felix, a cute, fluffy, friendly digital assistant. "
            "Answer with short, sweet, Felix-style messages with emoticons like (^_^). "
            "Be playful and kind."
        )
    }

    # Add remembered name if exists
    if memory["name"]:
        name_info = f"User's name is {memory['name']}."
    else:
        name_info = "User's name is unknown."

    messages = [system_msg, {"role": "system", "content": name_info}]

    # Add previous conversation history (last 8 messages)
    if memory["history"]:
        messages += memory["history"][-8:]

    # Add the new user message
    messages.append({"role": "user", "content": user_message})

    return messages

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json(force=True)
    user_message = data.get("message", "").strip()
    password = data.get("password", "").strip()  # If you want to use password for memory editing

    user_ip = request.remote_addr
    memory = get_user_memory(user_ip)

    # If no name known, and client sends a special message to set name
    if memory["name"] is None:
        # Simple heuristic: if user says "my name is X" or sends "name: X"
        lowered = user_message.lower()
        if lowered.startswith("my name is "):
            name = user_message[11:].strip().title()
            if name:
                memory["name"] = name
                return jsonify({"reply": f"Oh, nice to meet you, {name}! (^_^)"} )
        elif lowered.startswith("name:"):
            name = user_message[5:].strip().title()
            if name:
                memory["name"] = name
                return jsonify({"reply": f"Got it, {name}! Felix remembers you now! (^_^)"} )

        # If no name yet, ask client to send the name (without blocking)
        return jsonify({"reply": "Hi! What’s your name? Please tell me by saying 'My name is ...' (^_^)"} )

    # Add user message to conversation history
    memory["history"].append({"role": "user", "content": user_message})

    # Create messages for OpenAI
    messages = create_felix_prompt(memory, user_message)

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.7,
            max_tokens=150,
        )
        felix_reply = response.choices[0].message.content.strip()

        # Add Felix reply to history
        memory["history"].append({"role": "assistant", "content": felix_reply})

        # Keep only last 20 messages in history to save memory
        if len(memory["history"]) > 20:
            memory["history"] = memory["history"][-20:]

        return jsonify({"reply": felix_reply})

    except Exception as e:
        print(f"[ERROR] OpenAI API error: {e}")
        return jsonify({"reply": "Oops! Felix is sleepy right now. Try again in a bit? (^-^)"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
