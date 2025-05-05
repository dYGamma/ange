# auth/auth_service.py

import bcrypt
from sqlalchemy.exc import IntegrityError
from database.db_init import SessionLocal
from database.models import Employee
from datetime import datetime
from typing import Optional, Tuple


class AuthService:
    """
    Сервис регистрации и аутентификации пользователей.
    Хранилище — SQLite через SQLAlchemy.
    Пароли — bcrypt.
    """

    def __init__(self):
        # каждый вызов создаёт свою сессию
        self.db = SessionLocal()

    def register_user(
        self,
        username: str,
        full_name: str,
        position: str,
        password: str,
        hire_date_str: str
    ) -> Tuple[bool, str]:
        """
        Регистрирует нового пользователя.
        :return: (успех, сообщение)
        """
        # Валидация
        if not all([username.strip(), full_name.strip(), position.strip(),
                    password, hire_date_str.strip()]):
            return False, "Все поля обязательны"

        # Дата приёма
        try:
            hire_date = datetime.strptime(hire_date_str, "%Y-%m-%d").date()
        except ValueError:
            return False, "Неверный формат даты (ожидается YYYY-MM-DD)"

        # Хэш пароля
        pw_hash = bcrypt.hashpw(password.encode("utf-8"),
                                bcrypt.gensalt()).decode("utf-8")

        user = Employee(
            username=username.strip(),
            full_name=full_name.strip(),
            position=position.strip(),
            hire_date=hire_date,
            salary_rate=1.0,
            base_salary=0.0,
            password_hash=pw_hash
        )
        try:
            self.db.add(user)
            self.db.commit()
            return True, "Пользователь успешно зарегистрирован"
        except IntegrityError:
            self.db.rollback()
            return False, "Пользователь с таким логином уже существует"
        except Exception as e:
            self.db.rollback()
            return False, f"Ошибка регистрации: {e}"

    def authenticate_user(self, username: str, password: str) -> Optional[Employee]:
        """
        Ищет пользователя по логину и проверяет пароль.
        :return: объект Employee или None
        """
        user = (
            self.db.query(Employee)
            .filter(Employee.username == username.strip())
            .first()
        )
        if not user:
            return None

        if bcrypt.checkpw(password.encode("utf-8"),
                          user.password_hash.encode("utf-8")):
            return user
        return None

    def close(self) -> None:
        """Закрыть сессию при завершении работы."""
        self.db.close()
