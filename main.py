from agent import coding_agent

SKILLS_DIR = "skills"
SESSION_DIR = "session"
CHATS_MANIFEST_PATH = f"{SESSION_DIR}/chats_manifest.json"
SKILLS_INDEX_PATH = f"{SKILLS_DIR}/skills_index.json"

# initialize the chat and skills directiry
def init():
    import json
    import os

    os.makedirs(SKILLS_DIR, exist_ok=True)
    os.makedirs(SESSION_DIR, exist_ok=True)

    files_to_create = {
        CHATS_MANIFEST_PATH: [],
        SKILLS_INDEX_PATH: [],
    }

    for path, default_content in files_to_create.items():
        if not os.path.exists(path):
            with open(path, "w") as f:
                json.dump(default_content, f, indent=2)

# create a new chat
def new_chat():
    import json
    import os
    import random

    filename = os.path.join(SESSION_DIR, f"chat_{random.randint(100, 999)}.json")
    with open(filename, "w") as f:
        json.dump(messages, f)
    messages.clear()


# dream about the users input
def dream():
    print("Dreaming...")


messages = []
init()

while True:
    content = ""
    user_input = input("> ")

    if user_input.strip() == "/new-chat":
        new_chat()
        continue

    if user_input.strip() == "/dream":
        dream()
        continue
    
    messages.append({"role": "user", "content": user_input})
    response = coding_agent.run(messages, stream=True, stream_events=True)
    for event in response:
        if event.event == "RunContent":
            if event.content != None:
                content += event.content
                print(event.content, end="", flush=True)

    messages.append({"role": "assistant", "content": content})
    print()