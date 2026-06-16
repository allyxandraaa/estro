from datetime import date, datetime

from pydantic import BaseModel


class NotificationSchema(BaseModel):
    id: str
    type: str
    scheduled_date: date
    message: str
    is_read: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class NotificationsResponse(BaseModel):
    notifications: list[NotificationSchema]
    unread_count: int
