from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.user import User


class Group(Base):
    __tablename__ = "groups"

    group_name: Mapped[str] = mapped_column(String, nullable=False, unique=True, index=True)

    user: Mapped[list["User"]] = relationship(back_populates="groups")