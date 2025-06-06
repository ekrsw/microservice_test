from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional

from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    username: Mapped[str] = mapped_column(String, nullable=False, unique=True, index=True)
    full_name: Mapped[Optional[str]] = mapped_column(String, nullable=True, index=True)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_superuser: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
