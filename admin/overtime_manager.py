from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QMessageBox, QFormLayout, QComboBox, QLineEdit
)
from database.db_init import SessionLocal
from database.models import Overtime, Employee, ActionLog
from datetime import datetime

class OvertimeManager:
    def __init__(self, parent_user):
        self.db = SessionLocal()
        self.user = parent_user

    def open_dialog(self):
        dlg = QDialog()
        dlg.setWindowTitle("Управление переработками")
        layout = QVBoxLayout(dlg)

        emp_cb = QComboBox()
        emps = self.db.query(Employee).all()
        for e in emps:
            emp_cb.addItem(f"{e.id} – {e.full_name}", userData=e.id)

        form = QFormLayout()
        date_edit = QLineEdit(datetime.now().strftime("%Y-%m-%d"))
        hours_edit = QLineEdit()
        form.addRow("Сотрудник:", emp_cb)
        form.addRow("Дата (YYYY-MM-DD):", date_edit)
        form.addRow("Часы:", hours_edit)
        layout.addLayout(form)

        btn_add = QPushButton("Добавить")
        btn_add.clicked.connect(lambda: self.add(emp_cb, date_edit, hours_edit, dlg))
        btn_del = QPushButton("Удалить выбранный")
        layout.addWidget(btn_add)

        table = QTableWidget(0, 5)
        table.setHorizontalHeaderLabels(["ID","Сотрудник","Дата","Часы","Множитель"])
        layout.addWidget(table)
        self._refresh_table(table)
        layout.addWidget(btn_del)
        btn_del.clicked.connect(lambda: self.delete(table, dlg))

        dlg.exec_()

    def _refresh_table(self, table):
        recs = self.db.query(Overtime).all()
        table.setRowCount(len(recs))
        for i, o in enumerate(recs):
            table.setItem(i,0, QTableWidgetItem(str(o.id)))
            table.setItem(i,1, QTableWidgetItem(o.employee.full_name))
            table.setItem(i,2, QTableWidgetItem(o.date.strftime("%Y-%m-%d")))
            table.setItem(i,3, QTableWidgetItem(str(o.hours)))
            table.setItem(i,4, QTableWidgetItem(str(o.multiplier)))

    def add(self, emp_cb, date_edit, hours_edit, dlg):
        try:
            emp_id = emp_cb.currentData()
            dt = datetime.strptime(date_edit.text(), "%Y-%m-%d").date()
            hrs = float(hours_edit.text())
            o = Overtime(employee_id=emp_id, date=dt, hours=hrs)
            self.db.add(o)
            self.db.add(ActionLog(user_id=self.user.id, action="add_overtime",
                                  details=f"{emp_id},{dt},{hrs}"))
            self.db.commit()
            self.open_dialog()
        except Exception as e:
            QMessageBox.warning(dlg, "Ошибка", str(e))

    def delete(self, table, dlg):
        row = table.currentRow()
        if row<0:
            QMessageBox.warning(dlg,"Выберите запись")
            return
        oid = int(table.item(row,0).text())
        self.db.query(Overtime).filter(Overtime.id==oid).delete()
        self.db.add(ActionLog(user_id=self.user.id, action="del_overtime", details=str(oid)))
        self.db.commit()
        self.open_dialog()
