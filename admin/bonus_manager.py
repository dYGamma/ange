from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QMessageBox, QFormLayout, QComboBox, QLineEdit
)
from database.db_init import SessionLocal
from database.models import Bonus, Employee, ActionLog
from datetime import datetime

class BonusManager:
    def __init__(self, parent_user):
        self.db = SessionLocal()
        self.user = parent_user  # для логов

    def open_dialog(self):
        dlg = QDialog()
        dlg.setWindowTitle("Управление бонусами")
        layout = QVBoxLayout(dlg)

        # Выпадаем список сотрудников
        emp_cb = QComboBox()
        emps = self.db.query(Employee).all()
        for e in emps:
            emp_cb.addItem(f"{e.id} – {e.full_name}", userData=e.id)

        # Месяц и сумма
        form = QFormLayout()
        month_edit = QLineEdit(datetime.now().strftime("%m.%Y"))
        amount_edit = QLineEdit()
        form.addRow("Сотрудник:", emp_cb)
        form.addRow("Месяц (MM.YYYY):", month_edit)
        form.addRow("Сумма:", amount_edit)
        layout.addLayout(form)

        # Кнопки добавить/удалить/обновить
        btn_add = QPushButton("Добавить")
        btn_add.clicked.connect(lambda: self.add(emp_cb, month_edit, amount_edit, dlg))
        btn_del = QPushButton("Удалить выбранный")
        btn_del.clicked.connect(lambda: self.delete(table, dlg))
        layout.addWidget(btn_add)

        # Таблица всех бонусов
        table = QTableWidget(0, 4)
        table.setHorizontalHeaderLabels(["ID", "Сотрудник", "Месяц", "Сумма"])
        layout.addWidget(table)
        self._refresh_table(table)

        layout.addWidget(btn_del)
        dlg.exec_()

    def _refresh_table(self, table):
        recs = self.db.query(Bonus).all()
        table.setRowCount(len(recs))
        for i, b in enumerate(recs):
            table.setItem(i, 0, QTableWidgetItem(str(b.id)))
            table.setItem(i, 1, QTableWidgetItem(b.employee.full_name))
            table.setItem(i, 2, QTableWidgetItem(b.month))
            table.setItem(i, 3, QTableWidgetItem(str(b.amount)))

    def add(self, emp_cb, month_edit, amount_edit, dlg):
        try:
            emp_id = emp_cb.currentData()
            month  = month_edit.text().strip()
            amt    = float(amount_edit.text())
            b = Bonus(employee_id=emp_id, month=month, amount=amt)
            self.db.add(b)
            self.db.add(ActionLog(user_id=self.user.id, action="add_bonus",
                                  details=f"{emp_id},{month},{amt}"))
            self.db.commit()
            self.open_dialog()  # перезапуск для обновления
        except Exception as e:
            QMessageBox.warning(dlg, "Ошибка", str(e))

    def delete(self, table, dlg):
        row = table.currentRow()
        if row < 0:
            QMessageBox.warning(dlg, "Выберите запись")
            return
        bid = int(table.item(row,0).text())
        self.db.query(Bonus).filter(Bonus.id==bid).delete()
        self.db.add(ActionLog(user_id=self.user.id, action="del_bonus", details=str(bid)))
        self.db.commit()
        self.open_dialog()
