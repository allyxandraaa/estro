from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.dependencies.auth import get_current_user_id
from app.schemas.notifications import NotificationsResponse
from app.services.notification_service import NotificationService

router = APIRouter(prefix="/api/notifications", tags=["Notifications"])


@router.get("", response_model=NotificationsResponse)
async def get_notifications(
    user_id: UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
):
    service = NotificationService(session)
    return await service.get_and_generate(user_id)


@router.post("/read", status_code=status.HTTP_204_NO_CONTENT)
async def mark_all_read(
    user_id: UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
):
    service = NotificationService(session)
    await service.mark_all_read(user_id)
