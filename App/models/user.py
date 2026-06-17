from sqlalchemy import Column, Integer, String, Boolean, Enum, DateTime
from App.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    username = Column(String)
    email = Column(String, unique=True)
    password = Column(String)

    role = Column(Enum("user", "admin", name="user_roles"), default="user")
    is_active = Column(Boolean, default=False)
    token = Column(String, nullable=True)
    token_expiry = Column(DateTime, nullable=True)

    new_email = Column(String, nullable=True)
    new_password = Column(String, nullable=True)