from datetime import date

from sqlalchemy import Boolean, Date, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional

from app.db.base import Base


class Knowledge(Base):
    __tablename__ = "knowledge"

    title: Mapped[str] = mapped_column(String, nullable=False, unique=False, index=True)
    info_category: Mapped[int] = mapped_column(Integer, unique=False, nullable=False, default=0)
    key_words: Mapped[Optional[str]] = mapped_column(String, unique=False, nullable=True, index=True)
    importance: Mapped[Boolean] = mapped_column(Boolean, nullable=False, default=False)
    start_published: Mapped[Optional[date]] = mapped_column(Date, unique=False, nullable=True)
    end_published: Mapped[Optional[date]] = mapped_column(Date, unique=False, nullable=True)
    target: Mapped[int] = mapped_column(Integer, unique=False, nullable=False, default=0)
    question: Mapped[str] = mapped_column(String, unique=False, nullable=True, index=True)
    answer: Mapped[str] = mapped_column(String, unique=False, nullable=True, index=True)
    add_comments: Mapped[Optional[str]] = mapped_column(String, unique=False, nullable=True, index=True)
    remarks: Mapped[Optional[str]] = mapped_column(String, unique=False, nullable=True, index=True)

    status: Mapped[int] = mapped_column(Integer, unique=False, nullable=False, default=0)
