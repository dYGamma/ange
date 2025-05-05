# database/db_init.py
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models import Base

# Путь до файла БД: project_root/salary.db
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "salary.db")
DATABASE_URL = f"sqlite:///{DB_PATH}"

# Создаём движок SQLAlchemy
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False
)

# Фабрика сессий
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

def init_db():
    """
    Создаёт все таблицы, определённые в models.py, в SQLite базе.
    Вызывать при старте приложения.
    """
    Base.metadata.create_all(bind=engine)

# Если нужно автоматически инициализировать БД при импорте:
# init_db()