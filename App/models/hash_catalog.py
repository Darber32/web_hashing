from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text

from App.database import Base


class HashFunctionOption(Base):
    __tablename__ = "hash_function_options"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, nullable=False, index=True)
    implementation_path = Column(String, nullable=False)
    label = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    is_enabled = Column(Boolean, default=True, nullable=False)
    sort_order = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )


class CollisionMethodOption(Base):
    __tablename__ = "collision_method_options"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, nullable=False, index=True)
    implementation_path = Column(String, nullable=False)
    step_hash_function_code = Column(String, nullable=True)
    label = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    is_enabled = Column(Boolean, default=True, nullable=False)
    sort_order = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )
