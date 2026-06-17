from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from App.database import Base


class CompareEntry(Base):
    __tablename__ = "compare_entries"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=True, index=True)
    guest_token = Column(String, nullable=True, index=True)
    selection_key = Column(String, nullable=False, index=True)
    collision_method = Column(String, nullable=False, index=True)
    message = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    results = relationship(
        "CompareResult",
        back_populates="entry",
        cascade="all, delete-orphan",
        order_by="CompareResult.sort_order.asc(), CompareResult.id.asc()",
    )


class CompareResult(Base):
    __tablename__ = "compare_results"

    id = Column(Integer, primary_key=True, index=True)
    compare_entry_id = Column(
        Integer,
        ForeignKey("compare_entries.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    hash_function = Column(String, nullable=False, index=True)
    hash_label = Column(String, nullable=False)
    hash_value = Column(String, nullable=False)
    process_note = Column(Text, nullable=False)
    collision_note = Column(Text, nullable=False)
    initial_slot = Column(Integer, nullable=False)
    final_slot = Column(Integer, nullable=False)
    collision_detected = Column(Boolean, default=False, nullable=False)
    chain_position = Column(Integer, nullable=True)
    probe_count = Column(Integer, default=0, nullable=False)
    step_size = Column(Integer, nullable=True)
    sort_order = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    entry = relationship("CompareEntry", back_populates="results")

    @property
    def message(self):
        return self.entry.message if self.entry else ""
