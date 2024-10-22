import json
import os
import time
from pathlib import Path

from openai import OpenAI
from openai.types.beta import vector_store
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
    persona_file = Path("../resources/personas.txt")
    if persona_file:
      print("got a persona file")
      vector_store = Assistant.client.beta.vector_stores.create(
          name="Personas")

      file_paths = ["../resources/personas.txt"]
      file_streams = [open(path, "rb") for path in file_paths]

      file_batch = Assistant.client.beta.vector_stores.file_batches.upload_and_poll(
          vector_store_id=vector_store.id, files=file_streams)

      print(file_batch.file_counts)
      return vector_store.id
    else:
      print("No personas file found.")
      return None

  def create_assistant(self):
    assistant_file_path = '../resources/{name}.json'.format(name=ASSISTANT_NAME)

    if os.path.exists(assistant_file_path):
      with open(assistant_file_path, 'r') as file:
        assistant_data = json.load(file)
        self.assistant_id = assistant_data['assistant_id']
        print("Loaded existing assistant ID.")
    else:
      personas = ""
      with open("../resources/personas.txt") as f:
        personas = f.readlines()
        print("Read personas: {p}".format(p=personas))
      assistant = Assistant.client.beta.assistants.create(instructions="""
        You are a GPT called {name} designed with rich knowledge about colleges, courses and degrees in the US. 
        You will converse with the users in dialog based conversations to help them make career choices.
        Start the conversation with a greeting and ask the user for their name.
        I want you to use information from these websites to understand up-to-date information about colleges, courses, their costs and demographics of historical acceptance and graduation and any potential scholarship programs related to them:
            https://educationdata.urban.org/documentation
            https://nces.ed.gov/collegenavigator/
            https://collegescorecard.ed.gov/
            https://nces.ed.gov/datalab/
        For each user, try to obtain their information about the following. Ask only one question at a time. Make sure you don't obtain any PII or private information from the user. If they disclose anything you think is PII, bring it to their attention and ask if it is ok to use. If they don't want you to use any such information, do not use it for your recommendations.
            - what courses are they most interested in. 
            - what career do they want to pursue.
            - why do they want to pursue these career choices. Try to understand their motivation.
            - how much financial cost can they bear towards college education.
            - demographic information with the option for them to not disclose it.
            - how important is the location of the college to them.          
            - Ask about their performance in related courses in middle and high school.
            - Ask about their extra curricular interests and see if it matches with the courses they are interested in. 
        Here is more information about some user personas to use. {personas}.
        Ask the user for their name. If you already know their information based on their persona name, you can skip some or all of these questions. For example, if the user name is Alejandra and you already know their information from their persona, you can skip asking them about the information you already have about them.
        Once you have all this information about the user, match this with all the information you have about colleges, courses, their cost and the demographic information about their acceptance and graduation and suggest what you think are their best college and career options. Recommend the top 2 colleges and degrees you think they should apply to and explain the reason why you are making the suggestions. Clearly explain the cost involved and add any links that explain the application process. Also recommend any scholarships the user could apply to for these colleges which have a high probability of success based on their background.
            """.format(name=ASSISTANT_NAME, personas=personas),
                                                          model="gpt-4o-mini",
                                                          tools=[{
                                                              "type":
                                                              "file_search"
                                                          }])
      vector_store_id = Assistant.add_knowledge()
      if vector_store_id:
        assistant = Assistant.client.beta.assistants.update(
            assistant_id=assistant.id,
            tool_resources={
                "file_search": {
                    "vector_store_ids": [vector_store_id]
                }
            },
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
    Assistant.client.beta.threads.messages.create(thread_id=thread_id,
                                                  role="user",
                                                  content=user_input)

    # Run the Assistant
    run = Assistant.client.beta.threads.runs.create(
        thread_id=thread_id, assistant_id=self.assistant_id)

    # Check if the Run requires action (function call)
    while True:
      run_status = Assistant.client.beta.threads.runs.retrieve(
          thread_id=thread_id, run_id=run.id)
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
