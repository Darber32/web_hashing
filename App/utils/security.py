from passlib.context import CryptContext
import secrets

pwd_context = CryptContext(schemes=["bcrypt"])


def hash_password(password: str):
    return pwd_context.hash(password)


def verify_password(password: str, hashed: str):
    return pwd_context.verify(password, hashed)


def create_token():
    return secrets.token_urlsafe(32)