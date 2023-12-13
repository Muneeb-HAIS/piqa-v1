from flask import Flask, render_template, request,jsonify
from openai import OpenAI
import pandas as pd
import os

app = Flask(__name__)

os.environ["OPENAI_API_KEY"] = "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"
client = OpenAI()

# Load your data here (replace 'path_to_your_excel_file' with the actual path)
df = pd.read_excel(r'C:\Users\acer1\Downloads\Company Structure Dataset.xlsx')

# Convert DataFrame to JSON string
df_json = df.to_json(orient='split')

# System message to set the behavior of the assistant
system_message = {"role": "system", "content": df_json}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.form['user_input']

    # Check if the user wants to quit
    if user_input.lower() == 'quit':
        return render_template('index.html', user_input=user_input, assistant_response="Chatbot session ended.")

    # Add user input to the conversation
    user_messages = [{"role": "user", "content": user_input}]
    conversation = [system_message] + user_messages

    # Get the completion from OpenAI
    completion = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=conversation
    )

    # Display assistant's response
    assistant_response = completion.choices[0].message.content

    # Update the conversation with the assistant's response
    user_messages.append({"role": "assistant", "content": assistant_response})
    conversation = [system_message] + user_messages

    return render_template('index.html', user_input=user_input, assistant_response=assistant_response)

if __name__ == '__main__':
    app.run(debug=True)
