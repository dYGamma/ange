# config.py

import os
import bcrypt
import qt_material
from datetime import date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Константы
BCRYPT_ROUNDS = 12
DEFAULT_THEME = "light_blue.xml"

# Путь к файлу БД
DB_FILENAME  = os.path.join(os.path.dirname(__file__), "salary.db")
DATABASE_URL = f"sqlite:///{DB_FILENAME}"

# SQLAlchemy engine & session
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False
)
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

def apply_theme(app, theme: str = DEFAULT_THEME):
    """Применить тему qt-material."""
    qt_material.apply_stylesheet(app, theme)

def init_db():
    """Создать все таблицы, если их ещё нет."""
    from database.models import Base
    Base.metadata.create_all(bind=engine)

def seed_admin():
    """
    При первом запуске добавляем администратора-по-умолчанию:
      username = "admin"
      full_name= "Admin User"
      position = "Бухгалтер"
      password = "admin"
    """
    from database.models import Employee
    db = SessionLocal()

    exists = db.query(Employee).filter(Employee.username == "admin").first()
    if not exists:
        # хэш пароля
        pw_hash = bcrypt.hashpw(
            "admin".encode("utf-8"),
            bcrypt.gensalt(BCRYPT_ROUNDS)
        ).decode("utf-8")

        admin = Employee(
            username      = "admin",
            full_name     = "Admin User",
            position      = "Бухгалтер",
            hire_date     = date.today(),
            salary_rate   = 1.0,
            base_salary   = 0.0,
            password_hash = pw_hash
        )
        db.add(admin)
        db.commit()
    db.close()

# Инициализация при старте
init_db()
seed_admin()
