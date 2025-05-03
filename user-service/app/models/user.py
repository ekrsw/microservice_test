from sqlalchemy import Boolean, ForeignKey, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional
import uuid

from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    username: Mapped[str] = mapped_column(String, nullable=False, unique=True, index=True)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_supervisor: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    ctstage_name: Mapped[Optional[str]] = mapped_column(String, nullable=True, index=True)
    sweet_name: Mapped[Optional[str]] = mapped_column(String, nullable=True, index=True)
    group_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("groups.id"), nullable=False)

    groups: Mapped["Group"] = relationship(back_populates="user")