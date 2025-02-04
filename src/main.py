from flask import Flask, jsonify, request

from assistant import Assistant

# Start Flask app
app = Flask(__name__)

# Create new assistant or load existing
assistant = Assistant()
assistant.create_assistant()


@app.route('/', methods=['GET'])
def index():
  return jsonify("hello! Welcome to Elenchus")


@app.route('/start', methods=['GET'])
def start_conversation():
  """
  Start a conversation
  """
  print("Starting a new conversation...")
  thread_id = assistant.start_conversation()
  return jsonify({"thread_id": thread_id})


@app.route('/chat', methods=['POST'])
def chat():
  """
  Generate response
  """
  data = request.json
  thread_id = data.get('thread_id')
  user_input = data.get('message', '')

  if not thread_id:
    print("Error: Missing thread_id")  # Debugging line
    return jsonify({"error": "Missing thread_id"}), 400

  print(f"Received message: {user_input} for thread ID: {thread_id}")

  response = assistant.send_message(thread_id, user_input)
  return jsonify({"response": response})


# Run server
if __name__ == '__main__':
  app.run(host='0.0.0.0', port=8080)
