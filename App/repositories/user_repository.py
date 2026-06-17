from sqlalchemy.orm import Session
from App.models.user import User
from datetime import datetime


class User_Repository:

    def __init__(self, db: Session):
        self.db = db

    def get_by_email(self, email: str):
        return self.db.query(User).filter(User.email == email).first()

    def get_by_id(self, id: int):
        return self.db.query(User).filter(User.id == id).first()

    def get_by_token(self, token: str):
        return self.db.query(User).filter(User.token == token).first()

    def create(self, username, email: str, password: str, token: str, token_expiry: datetime):
        user = User(
            username=username,
            email=email,
            password=password,
            token=token,
            token_expiry=token_expiry,
            is_active=False
        )

        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)

        return user

    def activate(self, token: str):

        user = self.db.query(User).filter(User.token == token).first()

        if user:
            user.is_active = True
            user.token = None
            self.db.commit()

        return user

    def delete(self, id):
        user = self.get_by_id(id)
        if user:
            self.db.delete(user)
            self.db.commit()

    def add_token_email(self, id, token, token_expiry, new_email):
        user = self.get_by_id(id)
        
        if user:
            user.token = token,
            user.token_expiry = token_expiry,
            user.new_email = new_email
            self.db.commit()
            self.db.refresh(user)

        return user

    def add_token_password(self, id, token, token_expiry, password):
        user = self.get_by_id(id)
        
        if user:
            user.token = token
            user.token_expiry = token_expiry
            user.new_password = password
            self.db.commit()
            self.db.refresh(user)

        return user

    def add_token_password_by_email(self, email, token, token_expiry, password):
        user = self.get_by_email(email)
        
        if user:
            user.token = token,
            user.token_expiry = token_expiry,
            user.new_password = password
            self.db.commit()
            self.db.refresh(user)

        return user

    def reset_token(self, id):
        user = self.get_by_id(id)
        if user:
            user.token = None
            user.token_expiry = None
            self.db.commit()
            self.db.refresh(user)
    
    def reset_token_by_email(self, email):
        user = self.get_by_email(email)
        if user:
            user.token = None
            user.token_expiry = None
            self.db.commit()
            self.db.refresh(user)

    def edit_username(self, id, new_username):
        user = self.get_by_id(id)
        
        if user:
            user.username = new_username
            self.db.commit()
            self.db.refresh(user)

        return user

    def edit_email(self, token):
        user = self.db.query(User).filter(User.token == token).first()
        
        if user:
            user.email = user.new_email
            user.new_email = None
            user.token = None
            self.db.commit()
            self.db.refresh(user)

        return user

    def edit_password(self, token):
        user = self.db.query(User).filter(User.token == token).first()
        
        if user:
            user.password = user.new_password
            user.new_password = None
            user.token = None
            self.db.commit()
            self.db.refresh(user)

        return user