import requests
import pyttsx3
import webbrowser
import time

# Initialize text-to-speech
engine = pyttsx3.init()
engine.setProperty('rate', 175)

# Server URLs
SERVER_URL = "https://felix-brain-server.onrender.com/chat"
HEALTH_URL = "https://felix-brain-server.onrender.com/health"

offline_qa = {
    "what is your name": "I'm Felix! Your fluffy little digital friend! (^_^)",
    "who made you": "Crimson did! The best creator ever! (^_^)",
    "what time is it": f"The current time is {time.strftime('%I:%M %p')}",
    "tell me a joke": "Why did the computer sneeze? It had a virus! 🤧",
    "what is my name": "I can't remember your name offline. Connect me to the brain server! (^_^)",
    "bye": "Bye bye~ (^_^)"
}

game_list = [
    "Pet Simulator X", "Brookhaven 🏡", "Blox Fruits", "Doors 👁️",
    "Murder Mystery 2", "Adopt Me!", "Shindo Life", "Arsenal",
    "Jailbreak", "Tower of Hell", "Bee Swarm Simulator", "Evade",
    "BedWars", "Combat Warriors", "Natural Disaster Survival",
    "Anime Adventures", "Piggy", "Build A Boat", "Survive the Killer",
    "Nico's Nextbots"
]

def speak(text):
    try:
        engine.say(text)
        engine.runAndWait()
    except:
        pass

def help_section():
    print("\n🔍 Felix Help - Commands:")
    print("------------------------------------------------")
    print("musicplay <song name> - Play music on YouTube Music")
    print("play game - List games to play")
    print("play(<game name>) - Launch specified Roblox game")
    print("forgetname - Forget stored name and ask again")
    print("serverstatus - Check if server is online")
    print("help - Show this help")
    print("exit or bye - Exit Felix")
    print("------------------------------------------------\n")

def check_server_status():
    """Check if the server is online and working"""
    try:
        print("🔍 Checking server status...")
        res = requests.get(HEALTH_URL, timeout=10)
        if res.status_code == 200:
            data = res.json()
            print(f"✅ Server is online: {data.get('status', 'Unknown')}")
            print(f"🧠 OpenAI connected: {data.get('openai_connected', 'Unknown')}")
            return True
        else:
            print(f"❌ Server responded with status code: {res.status_code}")
            return False
    except requests.exceptions.Timeout:
        print("⏱️ Server is taking too long to respond (timeout)")
        return False
    except requests.exceptions.ConnectionError:
        print("🌐 Cannot connect to server (connection error)")
        return False
    except Exception as e:
        print(f"❌ Error checking server: {e}")
        return False

def play_game():
    print("\n🎮 Available Games:")
    for game in game_list:
        print("-", game)
    game = input("\nType the game name to launch: ").strip()
    if game in game_list:
        print(f"Launching {game} on Roblox...")
        webbrowser.open(f"https://www.roblox.com/games/search?Keyword={game.replace(' ', '%20')}")
    else:
        print("⚠️ Game not found in list.")

def fallback_offline_answer(msg):
    for q in offline_qa:
        if q in msg.lower():
            return offline_qa[q]
    return "Sorry, I'm offline and don't know how to answer that. 😥"

def send_to_server(message, retries=2):
    """Send message to server with retry logic"""
    for attempt in range(retries + 1):
        try:
            if attempt > 0:
                print(f"🔄 Retrying... (attempt {attempt + 1})")
                time.sleep(2)  # Wait 2 seconds between retries
            
            print("Felix: Sending information to server... 🚀")
            
            # Add headers to help with debugging
            headers = {
                'Content-Type': 'application/json',
                'User-Agent': 'Felix-Client/1.0'
            }
            
            res = requests.post(SERVER_URL, 
                              json={"message": message}, 
                              headers=headers,
                              timeout=30)
            
            # Check if request was successful
            res.raise_for_status()
            
            print("Felix: Server giving response... 🤖")
            response_data = res.json()
            
            # Check if response has the expected format
            if 'reply' not in response_data:
                raise ValueError(f"Invalid response format: {response_data}")
            
            return response_data
            
        except requests.exceptions.Timeout:
            print("⏱️ Server is taking too long to respond...")
            if attempt == retries:
                raise Exception("Server timeout after multiple attempts")
                
        except requests.exceptions.ConnectionError:
            print("🌐 Cannot connect to server...")
            if attempt == retries:
                raise Exception("Cannot connect to server")
                
        except requests.exceptions.HTTPError as e:
            print(f"❌ HTTP Error: {e.response.status_code}")
            if e.response.status_code == 500:
                print("💥 Server internal error - try again later")
            raise e
            
        except ValueError as e:
            print(f"❌ Invalid server response: {e}")
            raise e
            
    return None

def main():
    print("Felix Client started. Type 'help' for commands. (Felix Early Version, Expect Bugs)")
    print("Type 'serverstatus' to check if the server is online.\n")
    
    name_known = False
    
    # Check server status on startup
    if not check_server_status():
        print("⚠️ Warning: Server appears to be offline. You can still use offline features.\n")

    while True:
        user = input("You: ").strip()

        if user.lower() == "serverstatus":
            check_server_status()
            continue

        if user.lower() == "forgetname":
            try:
                response_data = send_to_server("CrimsonResetConfigData")
                reply = response_data.get("reply", "Memory reset confirmed")
                print(f"Felix: {reply}")
                speak("Okay! I forgot your name. Please tell me your name again.")
                name_known = False
            except Exception as e:
                print(f"⚠️ Error contacting server: {e}")
                print("Felix: I can't reset your memory right now, but you can try again later.")
            continue

        if user.lower() in ["exit", "quit", "bye"]:
            print("Felix: Bye bye~ (^_^)")
            speak("Bye bye~")
            break

        if user.lower() == "help":
            help_section()
            continue

        if user.lower() in ["play game", "playgame"]:
            play_game()
            continue

        if user.lower().startswith("play(") and user.endswith(")"):
            game = user[5:-1].strip()
            if game:
                print(f"Launching {game} on Roblox...")
                webbrowser.open(f"https://www.roblox.com/games/search?Keyword={game.replace(' ', '%20')}")
            continue

        if user.lower().startswith("musicplay"):
            search = user[9:].strip() or input("🎵 Music search: ")
            print(f"Opening YouTube Music for '{search}'...")
            webbrowser.open(f"https://music.youtube.com/search?q={search.replace(' ', '+')}")
            continue

        # Try to send message to server
        try:
            response_data = send_to_server(user)
            reply = response_data.get("reply", "🤖 No response from Felix.")
            status = response_data.get("status", "unknown")

            # Update name tracking
            if (not name_known) and ("my name is" in user.lower() or "nice to meet you" in reply.lower()):
                name_known = True

            if (not name_known) and ("please tell me your name" in reply.lower()):
                print("Felix: Hey! I don't know your name yet. Please say 'My name is ...' so I can remember you! (^_^)")
                speak("Hey! I don't know your name yet. Please say 'My name is ...' so I can remember you!")
            else:
                print("Felix:", reply)
                # Only speak if it's not an error
                if status != "error":
                    speak(reply.replace("💬", "").replace("(^_^)", "").strip())

        except Exception as e:
            print("Felix: The server might be sleeping or having issues. Let me try to help offline!")
            print(f"⚠️ Error: {e}")
            reply = fallback_offline_answer(user)
            print("Felix:", reply)
            speak(reply)

    input("\nPress Enter to exit...")  # Prevent immediate console close

if __name__ == "__main__":
    main()
