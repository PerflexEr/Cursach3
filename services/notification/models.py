from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Enum
import enum
from shared.database import Base, TimestampMixin


class NotificationType(str, enum.Enum):
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"


class NotificationPriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class NotificationTemplate(Base, TimestampMixin):
    __tablename__ = "notification_templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    subject = Column(String)
    body = Column(String)
    notification_type = Column(Enum(NotificationType))


class NotificationSettings(Base, TimestampMixin):
    __tablename__ = "notification_settings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    email_enabled = Column(Boolean, default=True)
    sms_enabled = Column(Boolean, default=False)
    push_enabled = Column(Boolean, default=True)
    email_address = Column(String)
    phone_number = Column(String)
    min_priority = Column(Enum(NotificationPriority), default=NotificationPriority.MEDIUM)


class Notification(Base, TimestampMixin):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    template_id = Column(Integer, ForeignKey("notification_templates.id"))
    notification_type = Column(Enum(NotificationType))
    priority = Column(Enum(NotificationPriority))
    subject = Column(String)
    body = Column(String)
    is_sent = Column(Boolean, default=False)
    sent_at = Column(String, nullable=True)
    error_message = Column(String, nullable=True) 