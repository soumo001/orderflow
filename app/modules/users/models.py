from sqlalchemy import Boolean, Column, ForeignKey, Index, String, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import TimestampedModel

user_roles = Table(
    "user_roles",
    TimestampedModel.metadata,
    Column("user_id", ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("role_id", ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
)


class Role(TimestampedModel):
    __tablename__ = "roles"

    name: Mapped[str] = mapped_column(String(40), unique=True, nullable=False)
    users: Mapped[list["User"]] = relationship(secondary=user_roles, back_populates="roles")


class User(TimestampedModel):
    __tablename__ = "users"
    __table_args__ = (Index("ix_users_email", "email"),)

    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    roles: Mapped[list[Role]] = relationship(secondary=user_roles, back_populates="users")
