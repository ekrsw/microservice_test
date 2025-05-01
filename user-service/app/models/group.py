from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Group(Base):
    __tablename__ = "groups"

    group_name: Mapped[str] = mapped_column(String, nullable=False, unique=True, index=True)