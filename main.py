from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from cbot import get_response
from models import SessionModel, db
import os

app = Flask(__name__)

login_password = os.environ.get('LOGIN_PASSWORD')

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sessions.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'xyz' ## CHANGE THIS TO SOMETHING SECURE ##
db.init_app(app)

LOGIN_PASSWORD_HASH = generate_password_hash(login_password)

# home route
@app.route('/')
def home():
    # Check if a session exists for the user
    session_id = request.cookies.get('session_id')
    session = SessionModel.query.filter_by(session_id=session_id).first()
    if session and not session.is_expired():
        # Session exists, show dashboard
        return redirect(url_for('bot'))
    else:
        # No session exists, redirect to login
        return redirect(url_for('login'))

# login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        password = request.form.get('password')
        if check_password_hash(LOGIN_PASSWORD_HASH, password):
            session_id = generate_session_id()
            chat_memory = ''

            session = SessionModel(session_id=session_id, chat_memory=chat_memory)
            db.session.add(session)
            db.session.commit()

            response = redirect(url_for('home'))
            response.set_cookie('session_id', session_id)
            return response
        else:
            return render_template('login.html', error="Invalid password")
    else:
        return render_template('login.html')

# logout route
@app.route('/logout', methods=['GET', 'POST'])
def logout():
    session_id = request.cookies.get('session_id')
    session = SessionModel.query.filter_by(session_id=session_id).first()
    if session and not session.is_expired():
        # Remove the session cookie
        response = redirect(url_for('login'))
        response.set_cookie('session_id', '', expires=0)
        session_id = request.cookies.get('session_id')
        session_to_delete = SessionModel.query.filter_by(session_id=session_id).first()
        db.session.delete(session_to_delete)
        db.session.commit()
        return response
    else:
        return redirect(url_for('login'))

# Helper function to generate a unique session ID
def generate_session_id():
    return str(datetime.now().timestamp())


#  Chatbot route
@app.route('/bot', methods=['GET', 'POST'])
def bot():
    session_id = request.cookies.get('session_id')
    session = SessionModel.query.filter_by(session_id=session_id).first()
    
    if session and not session.is_expired():
        if request.method == 'POST':
            session_id = request.cookies.get('session_id')
            answer_text = "➜ "
            response = get_response(session_id)
            return render_template("bot.html", answer_text=answer_text, session_id=session_id, response=response)

        else:
            return render_template('bot.html')
    else:
        return redirect(url_for('home'))

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


# running the Flask app
if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Create the database tables if they don't exist
    # app.run(debug=True, port=3000)
    app.run()

