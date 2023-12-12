from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin, LoginManager, current_user
from datetime import datetime, timedelta


login = LoginManager()
db = SQLAlchemy()


class SessionModel(db.Model):
    __tablename__ = 'session'

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(100), unique=True, nullable=False)
    chat_memory = db.Column(db.String(10000), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, session_id, chat_memory):
        self.session_id = session_id
        self.chat_memory = chat_memory

    def is_expired(self):
        expiration_time = self.created_at + timedelta(minutes=60)
        return expiration_time < datetime.utcnow()


