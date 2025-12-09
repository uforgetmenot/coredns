"""
数据库连接和会话管理
"""

import os
from sqlmodel import SQLModel, create_engine, Session
from app.config import settings

# 确保数据库目录存在
db_path = settings.database_url.replace("sqlite:///", "")
os.makedirs(os.path.dirname(db_path), exist_ok=True)

# 创建数据库引擎
engine = create_engine(
    settings.database_url,
    echo=settings.debug,
    connect_args={"check_same_thread": False},  # SQLite 特定配置
)


def create_db_and_tables():
    """创建所有数据库表"""
    SQLModel.metadata.create_all(engine)


def get_session():
    """
    获取数据库会话（用于依赖注入）

    使用方式：
    ```python
    @app.get("/items")
    def get_items(session: Session = Depends(get_session)):
        items = session.query(Item).all()
        return items
    ```
    """
    with Session(engine) as session:
        yield session
