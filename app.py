from flask import session,g
from flask import Flask, render_template, request,jsonify, flash, redirect, url_for
from flask_sqlalchemy import SQLAlchemy


from werkzeug.security import generate_password_hash, check_password_hash

from app_bk import chat, system_message,app,client




app = Flask(__name__)


app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = '12345'  # Change this to a secret key for your application


db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)

# Create the initial database
# Remove the db.create_all() call here
#db.create_all()
with app.app_context():
    db.create_all()


@app.before_request
def before_request():
    g.user = None
    if 'user_id' in request.cookies:
        user = User.query.get(request.cookies['user_id'])
        if user:
            g.user = user



@app.route('/')
def index():
    return redirect(url_for('login'))  # Redirect to the login page

@app.route('/chat', methods=['GET', 'POST'])
def chat():
    if request.method == 'POST':
        user_input = request.form['user_input']

        # Check if the user wants to quit
        if user_input.lower() == 'quit':
            return jsonify({"assistant_response": "Chatbot session ended."})
            #return render_template('index2.html', user_input=user_input, assistant_response="Chatbot session ended.")

        # Add user input to the conversation
        user_messages = [{"role": "user", "content": user_input}]
        conversation = [system_message] + user_messages

        try:
            # Get the completion from OpenAI
            completion = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=conversation
            )

            # Display assistant's response
            assistant_response = completion.choices[0].message.content

        except Exception as e:
            # Handle exceptions, you can print the exception for debugging purposes
            print(f"An error occurred: {e}")
            assistant_response = "Sorry, something went wrong. Please try again."

        # Update the conversation with the assistant's response
        user_messages.append({"role": "assistant", "content": assistant_response})
        conversation = [system_message] + user_messages

        # Return the assistant's response as JSON
        #return jsonify({"assistant_response": assistant_response})
        return jsonify({"assistant_response": assistant_response})
        #return render_template('index2.html', user_input=user_input, assistant_response=assistant_response)
        #return render_template('chat.html', assistant_response=assistant_response)

        #return render_template('index.html', user_input=user_input, assistant_response=assistant_response)

    # Handle GET request (display the chat form)
    return render_template('index3.html')  # You may need to create this template

    
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()

        if user:
            flash('User already exists. Please log in.', 'warning')
            return redirect(url_for('login'))  # Redirect to the login page

        hashed_password = generate_password_hash(password)

        new_user = User(username=username, password=hashed_password)

        db.session.add(new_user)
        db.session.commit()

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
