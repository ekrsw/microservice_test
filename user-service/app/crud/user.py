
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.schemas.user import UserCreate

class CRUDUser:
    # クラスレベルのロガーの初期化
    logger = get_logger(__name__)
    async def create(self, session: AsyncSession, obj_in: UserCreate) -> None:
        self.logger.info("Creating new user: {obj_in.username}")
