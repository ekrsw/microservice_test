from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.crud.exceptions import DuplicateGroupNameError, DatabaseIntegrityError
from app.models.group import Group
from app.schemas.group import GroupCreate


class CRUDGroup:
    # クラスレベルのロガーの初期化
    logger = get_logger(__name__)
    async def create(self, session: AsyncSession, obj_in: GroupCreate) -> Group:
        self.logger.info(f"Createing new group: {obj_in.group_name}")
        try:
            db_obj = Group(
                group_name=obj_in.group_name
            )
            session.add(db_obj)
            await session.flush()
            # commitはsessionのfinallyで行う
            self.logger.info(f"Group created successfully: {db_obj.id}")
        except IntegrityError as e:
            # エラーメッセージやコードを検査して、具体的なエラータイプを特定
            if "group_name" in str(e.orig).lower():
                self.logger.error(f"Failed to create group: '{db_obj.group_name}'")
                raise DuplicateGroupNameError("Group name already exists")
            else:
                # その他のIntegrityErrorの場合
                self.logger.error(f"Database integrity error while creating user: {str(e)}")
                raise DatabaseIntegrityError("Database integrity error") from e
        return db_obj

group_crud = CRUDGroup()