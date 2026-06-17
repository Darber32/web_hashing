from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text

from App.database import Base


class DemoEntry(Base):
    __tablename__ = "demo_entries"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=True, index=True)
    guest_token = Column(String, nullable=True, index=True)
    hash_function = Column(String, nullable=False, index=True)
    collision_method = Column(String, nullable=False, index=True)
    message = Column(Text, nullable=False)
    hash_value = Column(String, nullable=False)
    process_note = Column(Text, nullable=False)
    collision_note = Column(Text, nullable=False)
    initial_slot = Column(Integer, nullable=False)
    final_slot = Column(Integer, nullable=False)
    collision_detected = Column(Boolean, default=False, nullable=False)
    chain_position = Column(Integer, nullable=True)
    probe_count = Column(Integer, default=0, nullable=False)
    step_size = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
