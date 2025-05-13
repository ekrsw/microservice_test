from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional
import uuid

from app.db.base import Base


class Knowledge(Base):
    __tablename__ = "knowledge"

    # タイトル
    title: Mapped[str] = mapped_column(String, nullable=False, unique=False, index=True)
    # 情報カテゴリ
    info_category: Mapped[int] = mapped_column(Integer, unique=False, nullable=False, default=0)
    # キーワード
    key_words: Mapped[Optional[str]] = mapped_column(String, unique=False, nullable=True, index=True)
    # 重要
    importance: Mapped[Boolean] = mapped_column(Boolean, nullable=False, default=False)
    # 公開開始
    start_published: Mapped[Optional[date]] = mapped_column(Date, unique=False, nullable=True)
    end_published: Mapped[Optional[date]] = mapped_column(Date, unique=False, nullable=True)
    target: Mapped[int] = mapped_column(Integer, unique=False, nullable=False, default=0)
    question: Mapped[str] = mapped_column(String, unique=False, nullable=True, index=True)
    answer: Mapped[str] = mapped_column(String, unique=False, nullable=True, index=True)
    add_comments: Mapped[Optional[str]] = mapped_column(String, unique=False, nullable=True, index=True)
    remarks: Mapped[Optional[str]] = mapped_column(String, unique=False, nullable=True, index=True)

    status: Mapped[int] = mapped_column(Integer, unique=False, nullable=False, default=0)
    submitted_by: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, unique=False)
    submitted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), unique=False, nullable=True)

class InfoCategory(Base):
    __tablename__ = "info_category"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False, unique=True, index=True)