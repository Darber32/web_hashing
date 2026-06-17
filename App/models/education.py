from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from App.database import Base


class EducationPage(Base):
    __tablename__ = "education_pages"

    id = Column(Integer, primary_key=True, index=True)
    slug = Column(String, unique=True, nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    sort_order = Column(Integer, default=0, nullable=False)
    is_published = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    sections = relationship(
        "EducationSection",
        back_populates="page",
        passive_deletes=True,
    )


class EducationSection(Base):
    __tablename__ = "education_sections"
    __table_args__ = (
        UniqueConstraint("page_id", "slug", name="uq_education_sections_page_slug"),
    )

    id = Column(Integer, primary_key=True, index=True)
    page_id = Column(
        Integer,
        ForeignKey("education_pages.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    parent_id = Column(
        Integer,
        ForeignKey("education_sections.id", ondelete="CASCADE"),
        nullable=True,
    )
    slug = Column(String, nullable=False)
    title = Column(String, nullable=False)
    summary = Column(Text, nullable=True)
    content = Column(Text, nullable=True)
    sort_order = Column(Integer, default=0, nullable=False)
    is_published = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    page = relationship("EducationPage", back_populates="sections")
    parent = relationship(
        "EducationSection",
        remote_side=[id],
        back_populates="children",
    )
    children = relationship(
        "EducationSection",
        back_populates="parent",
        passive_deletes=True,
    )
