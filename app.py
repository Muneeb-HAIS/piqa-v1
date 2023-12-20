from flask import session,g
from flask import Flask, render_template, request,jsonify, flash, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import ForeignKey
from datetime import datetime
import logging
import sys


# Configure the logging
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

from werkzeug.security import generate_password_hash, check_password_hash

from app_bk import chat_bot as chat_bk , system_message,app,client




app = Flask(__name__)


# Configure the User database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = '12345'
user_db = SQLAlchemy(app)

class User(user_db.Model):
    id = user_db.Column(user_db.Integer, primary_key=True)
    username = user_db.Column(user_db.String(80), unique=True, nullable=False)
    password = user_db.Column(user_db.String(120), nullable=False)
    role = user_db.Column(user_db.String(50), nullable=False, default='user')

with app.app_context():
    user_db.create_all()

# Use the same instance of SQLAlchemy for the Conversation database
conversation_db = user_db


class Conversation(conversation_db.Model):
    id = conversation_db.Column(conversation_db.Integer, primary_key=True)
    user_id = conversation_db.Column(conversation_db.Integer, ForeignKey('user.id'), nullable=False)
    role = conversation_db.Column(conversation_db.String(50), nullable=False)
    content = conversation_db.Column(conversation_db.Text, nullable=False)
    model_info = conversation_db.Column(conversation_db.String(50))
    timestamp = conversation_db.Column(conversation_db.DateTime)
    feedback = conversation_db.Column(conversation_db.Text)
    feedback_details = conversation_db.Column(conversation_db.Text)
# Create the initial database
# Remove the db.create_all() call here
#db.create_all()
with app.app_context():
    conversation_db.create_all()


@app.before_request
def before_request():
    g.user = None
    user_id = request.cookies.get('user_id')
    if user_id:
        user = User.query.get(user_id)
        if user:
            g.user = user



@app.route('/')
def index():
    return redirect(url_for('login'))  # Redirect to the login page

@app.route('/submit-feedback', methods=['POST'])
def submit_feedback():
    feedback_data = request.json.get('feedback')
    feedback_details = request.json.get('details')

    if feedback_data:
        try:
            # Assuming feedback is related to the most recent conversation
            # You may need to modify this logic based on your application's needs
            user_id = g.user.id if g.user else None
            if user_id:
                conversation = Conversation(
                    user_id=user_id,
                    role='user',  # Or other appropriate role
                    content='Feedback submitted',  # Modify as needed
                    feedback=feedback_data,
                    feedback_details=feedback_details,
                    timestamp=datetime.utcnow()
                )
                conversation_db.session.add(conversation)
                conversation_db.session.commit()
                return jsonify({"status": "success", "message": "Feedback submitted successfully."})
            else:
                return jsonify({"status": "error", "message": "User not identified."})
        except Exception as e:
            print(f"An error occurred while inserting feedback: {e}")
            return jsonify({"status": "error", "message": "Error processing feedback."})
    else:
        return jsonify({"status": "error", "message": "Invalid feedback data."})

@app.route('/chat', methods=['GET', 'POST'])
def chat():
    if request.method == 'POST':
        user_input = request.json.get('user_input')
        feedback = request.json.get('feedback')
        messages = request.json.get('messages')

        # Check if the user wants to quit
        user = g.user

        if user_input.lower() == 'quit':
            return jsonify({"assistant_response": "Chatbot session ended."})

        if user:
            if user.role == 'admin':
                # Add user input to the conversation
                user_messages = [{"role": "user", "content": user_input}]
                if feedback is not None:
                    user_messages.append({"role": "assistant", "content": feedback})

                conversation = [system_message] + user_messages

                try:
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

                    # Store the conversation in the database
                    model_info = "gpt-3.5-turbo"  # Modify this based on the actual model used
                    timestamp = datetime.utcnow()
                    
                    logging.debug(f"Sending request to OpenAI API: {conversation}")

                    try:
                        for message in conversation:
                            db_message = Conversation(
                                user_id=g.user.id,
                                role=message["role"],
                                content=message["content"],
                                model_info=model_info,
                                timestamp=timestamp
                            )
                            if "feedback" in message:
                                db_message.feedback = message["feedback"]

                            print(f"Inserting into database: {db_message}")
                            conversation_db.session.add(db_message)
                            conversation_db.session.commit()
                    except Exception as e:
                        conversation_db.session.rollback()
                        print(f"An error occurred while inserting into the database: {e}")
                        raise

                except Exception as e:
                    # Handle exceptions, you can print the exception for debugging purposes
                    print(f"An error occurred: {e}")
                    assistant_response = "Sorry, something went wrong. Please try again."

            elif user.role == 'user':
                # Process user-level queries
                # Implement logic to handle queries based on user access
                assistant_response = "You do not have permission to perform this action."

            else:
                # Handle other roles as needed
                assistant_response = "Invalid role. Contact the administrator."

            return jsonify({"assistant_response": assistant_response})

    return render_template('index3.html')


    
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']  # Add this line to get the access level

        user = User.query.filter_by(username=username).first()

        if user:
            flash('User already exists. Please log in.', 'warning')
            return redirect(url_for('login'))

        hashed_password = generate_password_hash(password)

        new_user = User(username=username, password=hashed_password, role=role) 

        user_db.session.add(new_user)
        user_db.session.commit()

        flash('Account created successfully!', 'success')
        return redirect(url_for('login'))

    return render_template('signup.html')

    
@app.route('/login', methods=['GET', 'POST'])
def login():
    if g.user:
        flash('You are already logged in.', 'info')
        return redirect(url_for('chat'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if username and password:
            user = User.query.filter_by(username=username).first()

            if user and check_password_hash(user.password, password):
                flash('Login successful!', 'success')
                response = redirect(url_for('chat'))
                response.set_cookie('user_id', str(user.id))  # Store user id in a cookie
                return response

            else:
                flash('Invalid username or password. Please try again.', 'warning')
                return render_template('login.html')

        else:
            return render_template('login.html')

    else:
        return render_template('login.html')
    
    
@app.route('/logout')
def logout():
    response = redirect(url_for('login'))
    response.delete_cookie('user_id')  # Remove the user_id cookie
    flash('You have been logged out.', 'info')
    return response
    




if __name__ == '__main__':
    #db.create_all()  # Create the initial database here
    app.run(debug=True)
