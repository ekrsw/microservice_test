import asyncio

from sqlalchemy import inspect

from app.crud.user import user_crud
from app.crud.group import group_crud
from app.schemas.user import UserCreate
from app.schemas.group import GroupCreate
from app.db.init import Database
from app.db.session import async_engine, AsyncSessionLocal


async def main():
    # データベース初期化処理
    db = Database()
    await db.init()

    # 登録するユーザー情報
    user_in = UserCreate(
        group_name="test_group"
    )
    async with AsyncSessionLocal() as session:
        await group_crud.create(session, user_in)
        await session.commit()
        
if __name__ == "__main__":
    asyncio.run(main())