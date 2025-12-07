from datetime import datetime, timezone

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from echonotify.infrastructure.database.models import Base


class UserProfile(Base):
    __tablename__ = "user_profile"
    id: Mapped[int] = mapped_column(
        primary_key=True, nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(nullable=False)
    email: Mapped[str] = mapped_column(nullable=False, unique=True, index=True)
    password: Mapped[str] = mapped_column(nullable=False)
    google_sub: Mapped[str] = mapped_column(nullable=True, unique=True)
    is_google_account: Mapped[bool] = mapped_column(
        default=False, nullable=False
    )
    vk_sub: Mapped[str] = mapped_column(nullable=True, unique=True)
    is_vk_account: Mapped[bool] = mapped_column(default=False, nullable=True)

    statistics = relationship(
        "UserStatistics", back_populates="user", uselist=False
    )
    stars = relationship("UserStars", back_populates="user", uselist=False)


class RefreshToken(Base):
    __tablename__ = "refresh_token"
    id: Mapped[int] = mapped_column(primary_key=True, nullable=False)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("user_profile.id"), nullable=False
    )
    token: Mapped[str] = mapped_column(nullable=False, unique=True)
    expires_at: Mapped[datetime] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        default=datetime.now(tz=timezone.utc)
    )
