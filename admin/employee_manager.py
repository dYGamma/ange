from PyQt5.QtWidgets import (
    QDialog, QFormLayout, QLineEdit, QDateEdit,
    QDialogButtonBox, QMessageBox
)
from PyQt5.QtCore import Qt, QDate
from database.db_init import SessionLocal
from database.models import Employee
import bcrypt
from datetime import datetime


class EmployeeManager:
    def __init__(self):
        self.db = SessionLocal()

    def search(self, term: str):
        q = self.db.query(Employee)
        if term:
            if term.isdigit():
                q = q.filter(Employee.id == int(term))
            else:
                q = q.filter(Employee.full_name.ilike(f"%{term}%"))
        return q.order_by(Employee.id).all()

    def delete(self, emp_id: int):
        self.db.query(Employee).filter(Employee.id == emp_id).delete()
        self.db.commit()

    def add_employee_dialog(self, parent=None) -> bool:
        dlg = QDialog(parent)
        dlg.setWindowTitle("Добавить сотрудника")
        form = QFormLayout(dlg)

        # Обязательные поля
        le_username = QLineEdit();      form.addRow("Логин (username):", le_username)
        le_full_name = QLineEdit();     form.addRow("ФИО:",             le_full_name)
        le_password = QLineEdit();      form.addRow("Пароль:",          le_password)
        le_password.setEchoMode(QLineEdit.Password)

        le_position = QLineEdit();      form.addRow("Должность:",       le_position)
        de_hire_date = QDateEdit(QDate.currentDate())
        de_hire_date.setCalendarPopup(True)
        form.addRow("Дата приёма:",       de_hire_date)

        le_rate = QLineEdit();          form.addRow("Ставка:",           le_rate)
        le_base = QLineEdit();          form.addRow("Оклад:",            le_base)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            orientation=Qt.Horizontal, parent=dlg
        )
        form.addRow(buttons)

        buttons.accepted.connect(dlg.accept)
        buttons.rejected.connect(dlg.reject)

        # Показываем диалог
        result = dlg.exec_()
        if result != QDialog.Accepted:
            return False

        # Сбор и валидация данных
        username = le_username.text().strip()
        full_name = le_full_name.text().strip()
        password = le_password.text()
        position = le_position.text().strip()
        hire_date = de_hire_date.date().toPyDate()
        try:
            rate = float(le_rate.text())
            base = float(le_base.text())
        except ValueError:
            QMessageBox.warning(dlg, "Ошибка", "Ставка и оклад должны быть числами")
            return False

        if not (username and full_name and password and position):
            QMessageBox.warning(dlg, "Ошибка", "Заполните все поля")
            return False

        # Хэшируем пароль
        pw_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

        # Создаём запись
        new_emp = Employee(
            username=username,
            full_name=full_name,
            position=position,
            hire_date=hire_date,
            salary_rate=rate,
            base_salary=base,
            password_hash=pw_hash
        )
        try:
            self.db.add(new_emp)
            self.db.commit()
            QMessageBox.information(dlg, "Готово", "Сотрудник добавлен")
            return True
        except Exception as e:
            self.db.rollback()
            QMessageBox.critical(dlg, "Ошибка при добавлении", str(e))
            return False
