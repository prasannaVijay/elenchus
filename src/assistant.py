# assistant.py

import json
import os
import time
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()

ASSISTANT_NAME = os.environ.get('ASSISTANT_NAME', 'studor')
OPENAI_API_KEY = os.environ['OPENAI_API_KEY']

if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY is not set in the environment variables.")


class Assistant(object):
    client = OpenAI(api_key=OPENAI_API_KEY)

    def __init__(self) -> None:
        self.assistant_id = ""

    @staticmethod
    def add_knowledge():
        # Ensure correct path handling using os.path.join
        personas_file_path = os.path.join(os.path.dirname(__file__), '../resources/personas.txt')
        persona_file = Path(personas_file_path)

        if persona_file.is_file():
            print("Got a persona file")
            vector_store = Assistant.client.beta.vector_stores.create(name="Personas")

            file_paths = [personas_file_path]
            file_streams = [open(path, "rb") for path in file_paths]

            file_batch = Assistant.client.beta.vector_stores.file_batches.upload_and_poll(
                vector_store_id=vector_store.id, files=file_streams
            )

            print(file_batch.file_counts)
            return vector_store.id
        else:
            print("No personas file found.")
            return None

    def create_assistant(self):
        # Use os.path.join to handle paths correctly
        assistant_file_path = os.path.join(os.path.dirname(__file__), '../resources/{name}.json'.format(name=ASSISTANT_NAME))

        if os.path.exists(assistant_file_path):
            with open(assistant_file_path, 'r') as file:
                assistant_data = json.load(file)
                self.assistant_id = assistant_data['assistant_id']
                print("Loaded existing assistant ID.")
        else:
            personas = ""
            with open(os.path.join(os.path.dirname(__file__), '../resources/personas.txt')) as f:
                personas = f.readlines()
                print(f"Read personas: {personas}")
            assistant = Assistant.client.beta.assistants.create(instructions="""
                You are a GPT called {name} designed with rich knowledge about colleges, courses, and degrees in the US. 
                You will converse with users in dialog-based conversations to help them make career choices.
                Start the conversation with a greeting and ask the user for their name.
                Use the provided personas and information to guide the conversation.
                """.format(name=ASSISTANT_NAME, personas=personas), model="gpt-4o-mini", tools=[{"type": "file_search"}])
            
            vector_store_id = Assistant.add_knowledge()
            if vector_store_id:
                assistant = Assistant.client.beta.assistants.update(
                    assistant_id=assistant.id,
                    tool_resources={"file_search": {"vector_store_ids": [vector_store_id]}}
                )

            with open(assistant_file_path, 'w') as file:
                json.dump({'assistant_id': assistant.id}, file)
                print("Created a new assistant and saved the ID.")

            self.assistant_id = assistant.id

    def start_conversation(self):
        thread = Assistant.client.beta.threads.create()
        print(f"New thread created with ID: {thread.id}")
        return thread.id

    def send_message(self, thread_id, user_input):
        # Add the user's message to the thread
        Assistant.client.beta.threads.messages.create(thread_id=thread_id, role="user", content=user_input)

        # Run the Assistant
        run = Assistant.client.beta.threads.runs.create(thread_id=thread_id, assistant_id=self.assistant_id)

        # Check if the Run requires action (function call)
        while True:
            run_status = Assistant.client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run.id)
            print(f"Run status: {run_status.status}")
            if run_status.status == 'completed':
                break
            time.sleep(1)  # Wait for a second before checking again

        # Retrieve and return the latest message from the assistant
        messages = Assistant.client.beta.threads.messages.list(thread_id=thread_id)
        response = messages.data[0].content[0].text.value

        print(f"Assistant response: {response}")  # Debugging line
        return response


assistant = Assistant()
