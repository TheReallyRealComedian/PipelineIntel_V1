# backend/services/auth_service.py
from sqlalchemy.orm import Session
from ..models import User

def find_user_by_username(db_session: Session, username: str):
    """Finds a user by their username."""
    return db_session.query(User).filter_by(username=username).first()

def create_user(db_session: Session, username: str, password: str):
    """Creates a new user, hashes the password, and adds to the session."""
    if not username or not password:
        return None, "Username and password are required."

    if find_user_by_username(db_session, username):
        return None, "Username already exists. Please choose a different one."

    new_user = User(username=username)
    new_user.set_password(password)
    db_session.add(new_user)
    db_session.commit()
    return new_user, "Registration successful! Please log in."

def authenticate_user(db_session: Session, username: str, password: str):
    """
    Authenticates a user. Returns the user object on success, None on failure.
    """
    user = find_user_by_username(db_session, username)
    if user and user.check_password(password):
        return user
    return None