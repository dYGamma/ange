# admin/excel_exporter.py

import os
from openpyxl import Workbook
from datetime import datetime
from database.db_init import SessionLocal
from database.models import Salary, Employee

class ExcelExporter:
    """
    Экспорт расчётных данных в Excel.
    """

    def __init__(self):
        self.db = SessionLocal()

    def export_salary_report(self, month: str) -> str:
        """
        Собирает все записи Salary за указанный месяц и кладёт их в xlsx.
        Возвращает путь к сохранённому файлу.
        """
        records = (
            self.db.query(Salary)
            .filter(Salary.month == month)
            .all()
        )

        wb = Workbook()
        ws = wb.active
        ws.title = f"Зарплата {month}"

        # Заголовок
        headers = ["ID", "ФИО", "Месяц", "Премии", "Начислено", "НДФЛ", "К выплате"]
        ws.append(headers)

        for sal in records:
            emp = self.db.query(Employee).get(sal.employee_id)
            ws.append([
                sal.employee_id,
                emp.full_name,
                sal.month,
                sal.bonus,
                sal.gross,   # <-- здесь было total_income
                sal.ndfl,
                sal.payout
            ])

        # Авто-подгонка ширины колонок
        for col in ws.columns:
            max_length = 0
            col_letter = col[0].column_letter
            for cell in col:
                v = str(cell.value or "")
                if len(v) > max_length:
                    max_length = len(v)
            ws.column_dimensions[col_letter].width = max_length + 2

        # Сохраняем
        fn = f"salary_report_{month.replace('.', '_')}_{datetime.now():%Y%m%d%H%M%S}.xlsx"
        path = os.path.abspath(fn)
        wb.save(path)
        return path
