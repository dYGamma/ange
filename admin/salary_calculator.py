# admin/salary_calculator.py

from sqlalchemy.orm import Session
from database.models import Employee, Salary, Bonus, Overtime
from datetime import datetime


class SalaryCalculator:
    """
    Сервис полного расчёта зарплаты за месяц с учётом:
    - базового оклада и коэффициента ставки
    - бонусов из таблицы bonuses
    - сверхурочных из таблицы overtimes
    - НДФЛ (13%) и отчислений для компании
    """

    TAX_RATE = 0.13
    CONTRIBUTION_PFR = 0.22
    CONTRIBUTION_FOMS = 0.051
    CONTRIBUTION_FSS = 0.029

    def __init__(self, db: Session):
        self.db = db

    def current_month(self) -> str:
        """Возвращает нынешний месяц в формате MM.YYYY"""
        return datetime.now().strftime("%m.%Y")

    def compute_month(self, month: str = None):
        """
        Запускает полный расчёт для всех сотрудников за указанный месяц.
        Если month не передан, берётся current_month().
        """
        if month is None:
            month = self.current_month()

        employees = self.db.query(Employee).all()
        for emp in employees:
            base = emp.base_salary or 0.0
            rate = emp.salary_rate or 1.0
            gross_base = base * rate

            # Сумма бонусов за месяц
            b_list = (
                self.db.query(Bonus)
                .filter(Bonus.employee_id == emp.id, Bonus.month == month)
                .all()
            )
            total_bonus = sum(b.amount for b in b_list)

            # Сумма сверхурочных за месяц
            ot_list = (
                self.db.query(Overtime)
                .filter(
                    Overtime.employee_id == emp.id,
                    Overtime.date.like(f"%.{month}")
                )
                .all()
            )
            total_overtime = sum(
                o.hours * (base / 160) * o.multiplier for o in ot_list
            )

            total_income = gross_base + total_bonus + total_overtime
            ndfl = round(total_income * self.TAX_RATE, 2)
            payout = round(total_income - ndfl, 2)
            # Полные затраты компании: чистый доход + взносы
            company_costs = round(
                total_income * (1 
                                + self.CONTRIBUTION_PFR 
                                + self.CONTRIBUTION_FOMS 
                                + self.CONTRIBUTION_FSS),
                2
            )

            # Обновляем или создаём запись в таблице salaries
            rec = (
                self.db.query(Salary)
                .filter(Salary.employee_id == emp.id, Salary.month == month)
                .first()
            )
            if not rec:
                rec = Salary(employee_id=emp.id, month=month)
                self.db.add(rec)

            rec.bonus          = total_bonus
            rec.overtime_sum   = total_overtime
            rec.gross          = total_income
            rec.ndfl           = ndfl
            rec.payout         = payout
            rec.company_costs  = company_costs

        # Сохраняем всё в БД
        self.db.commit()
