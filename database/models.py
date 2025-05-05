# database/models.py

from sqlalchemy import (
    Column, Integer, String, Float, Date, DateTime, ForeignKey, Text, Boolean
)
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()


class Employee(Base):
    __tablename__ = "employees"

    id            = Column(Integer, primary_key=True, autoincrement=True)
    username      = Column(String, nullable=False, unique=True, index=True)  # логин для входа
    full_name     = Column(String, nullable=False)                           # ФИО для отображения
    position      = Column(String, nullable=False)
    hire_date     = Column(Date, nullable=False)
    salary_rate   = Column(Float, nullable=False)
    base_salary   = Column(Float, nullable=False)
    password_hash = Column(String, nullable=False)

    # связи
    bonuses    = relationship(
        "Bonus", back_populates="employee", cascade="all, delete-orphan"
    )
    overtimes  = relationship(
        "Overtime", back_populates="employee", cascade="all, delete-orphan"
    )
    salaries   = relationship(
        "Salary", back_populates="employee", cascade="all, delete-orphan"
    )
    logs       = relationship(
        "ActionLog", back_populates="user", cascade="all, delete-orphan"
    )
    sent_msgs  = relationship(
        "SupportMessage",
        back_populates="sender",
        foreign_keys="SupportMessage.from_user_id",
        cascade="all, delete-orphan",
    )
    recv_msgs  = relationship(
        "SupportMessage",
        back_populates="receiver",
        foreign_keys="SupportMessage.to_user_id",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"<Employee(id={self.id}, username={self.username}, full_name={self.full_name})>"


class Salary(Base):
    __tablename__ = "salaries"

    id            = Column(Integer, primary_key=True, autoincrement=True)
    employee_id   = Column(
        Integer, ForeignKey("employees.id", ondelete="CASCADE"), nullable=False
    )
    month         = Column(String(7), default="", nullable=False)   # формат MM.YYYY
    bonus         = Column(Float,   default=0.0, nullable=False)
    overtime_sum  = Column(Float,   default=0.0, nullable=False)
    gross         = Column(Float,   default=0.0, nullable=False)
    ndfl          = Column(Float,   default=0.0, nullable=False)
    payout        = Column(Float,   default=0.0, nullable=False)
    company_costs = Column(Float,   default=0.0, nullable=False)

    employee = relationship("Employee", back_populates="salaries")

    def __repr__(self):
        return (
            f"<Salary(id={self.id}, emp_id={self.employee_id}, "
            f"month={self.month}, payout={self.payout})>"
        )


class Bonus(Base):
    __tablename__ = "bonuses"

    id           = Column(Integer, primary_key=True, autoincrement=True)
    employee_id  = Column(
        Integer, ForeignKey("employees.id", ondelete="CASCADE"), nullable=False
    )
    month        = Column(String(7), nullable=False)  # формат MM.YYYY
    amount       = Column(Float, nullable=False)
    type         = Column(String, default="standard")
    created_at   = Column(DateTime, default=datetime.utcnow)

    employee = relationship("Employee", back_populates="bonuses")

    def __repr__(self):
        return (
            f"<Bonus(id={self.id}, emp_id={self.employee_id}, "
            f"month={self.month}, amount={self.amount})>"
        )


class Overtime(Base):
    __tablename__ = "overtimes"

    id           = Column(Integer, primary_key=True, autoincrement=True)
    employee_id  = Column(
        Integer, ForeignKey("employees.id", ondelete="CASCADE"), nullable=False
    )
    date         = Column(Date, nullable=False)
    hours        = Column(Float, nullable=False)
    multiplier   = Column(Float, default=1.5)
    created_at   = Column(DateTime, default=datetime.utcnow)

    employee = relationship("Employee", back_populates="overtimes")

    def __repr__(self):
        return (
            f"<Overtime(id={self.id}, emp_id={self.employee_id}, "
            f"date={self.date}, hours={self.hours}, multiplier={self.multiplier})>"
        )


class ActionLog(Base):
    __tablename__ = "action_logs"

    id       = Column(Integer, primary_key=True, autoincrement=True)
    user_id  = Column(Integer, ForeignKey("employees.id", ondelete="SET NULL"))
    action   = Column(String, nullable=False)
    details  = Column(Text)
    ts       = Column(DateTime, default=datetime.utcnow)

    user = relationship("Employee", back_populates="logs")

    def __repr__(self):
        return (
            f"<ActionLog(id={self.id}, user_id={self.user_id}, "
            f"action={self.action}, ts={self.ts})>"
        )


class SupportMessage(Base):
    __tablename__ = "support_messages"

    id           = Column(Integer, primary_key=True, autoincrement=True)
    from_user_id = Column(
        Integer, ForeignKey("employees.id", ondelete="CASCADE"), nullable=False
    )
    to_user_id   = Column(
        Integer, ForeignKey("employees.id", ondelete="CASCADE"), nullable=False
    )
    text         = Column(Text, nullable=False)
    ts           = Column(DateTime, default=datetime.utcnow)
    is_read      = Column(Boolean, default=False, nullable=False)

    sender   = relationship(
        "Employee",
        back_populates="sent_msgs",
        foreign_keys=[from_user_id],
    )
    receiver = relationship(
        "Employee",
        back_populates="recv_msgs",
        foreign_keys=[to_user_id],
    )

    def __repr__(self):
        return (
            f"<SupportMessage(id={self.id}, from={self.from_user_id}, "
            f"to={self.to_user_id}, is_read={self.is_read}, ts={self.ts})>"
        )
