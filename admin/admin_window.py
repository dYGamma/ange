# admin/admin_window.py

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTabWidget, QTableWidget, QTableWidgetItem,
    QLabel, QLineEdit, QMessageBox, QHeaderView, QComboBox, QFormLayout, QTextEdit, QFileDialog
)
from PyQt5.QtCore import Qt
import matplotlib.pyplot as plt
from datetime import datetime
from sqlalchemy.orm import joinedload

from database.db_init import SessionLocal
from database.models import (
    Employee, Salary, Bonus, Overtime,
    ActionLog, SupportMessage
)
from admin.employee_manager import EmployeeManager
from admin.salary_calculator import SalaryCalculator
from admin.excel_exporter import ExcelExporter


class AdminWindow(QMainWindow):
    def __init__(self, user):
        super().__init__()
        self.user = user
        self.setWindowTitle(f"Панель бухгалтера — {user.full_name}")
        self.resize(1524, 768)

        # Инициализация БД и сервисов
        self.db         = SessionLocal()
        self.manager    = EmployeeManager()
        self.calculator = SalaryCalculator(self.db)
        self.exporter   = ExcelExporter()

        # Создание вкладок
        tabs = QTabWidget()
        tabs.addTab(self._create_employees_tab(),  "Сотрудники")
        tabs.addTab(self._create_salary_tab(),     "Расчёт")
        tabs.addTab(self._create_bonus_tab(),      "Бонусы")
        tabs.addTab(self._create_overtime_tab(),   "Переработки")
        tabs.addTab(self._create_report_tab(),     "Отчёты")
        tabs.addTab(self._create_messages_tab(),   "Сообщения")

        central = QWidget()
        layout  = QVBoxLayout(central)
        layout.addWidget(tabs)
        self.setCentralWidget(central)

    def _setup_table(self, table: QTableWidget, headers: list[str]):
        """
        Общая настройка таблицы:
        - Растягивание колонок
        - Перенос текста
        - Скрытие скроллбаров
        - Автоматическое изменение высоты строк
        """
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)
        hdr = table.horizontalHeader()
        hdr.setSectionResizeMode(QHeaderView.Stretch)
        table.setWordWrap(True)
        table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        table.resizeRowsToContents()

    # ————————— Таблица «Сотрудники» —————————————————————————————
    def _create_employees_tab(self) -> QWidget:
        w    = QWidget()
        vlay = QVBoxLayout(w)
        hlay = QHBoxLayout()

        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Поиск по ФИО или ID")
        btn_search = QPushButton("Поиск")
        btn_search.clicked.connect(self._refresh_employees)

        btn_add = QPushButton("Добавить")
        btn_add.clicked.connect(self._handle_add_employee)

        btn_del = QPushButton("Удалить")
        btn_del.clicked.connect(self._delete_employee)

        for wdg in (self.search_edit, btn_search, btn_add, btn_del):
            hlay.addWidget(wdg)
        hlay.addStretch()
        vlay.addLayout(hlay)

        self.emp_table = QTableWidget()
        self._setup_table(self.emp_table, [
            "ID", "ФИО", "Должность", "Дата приёма", "Ставка", "Оклад"
        ])
        vlay.addWidget(self.emp_table)
        self._refresh_employees()

        return w

    def _refresh_employees(self):
        term = self.search_edit.text().strip()
        emps = self.manager.search(term)
        self.emp_table.setRowCount(len(emps))
        for i, e in enumerate(emps):
            self.emp_table.setItem(i, 0, QTableWidgetItem(str(e.id)))
            self.emp_table.setItem(i, 1, QTableWidgetItem(e.full_name))
            self.emp_table.setItem(i, 2, QTableWidgetItem(e.position))
            self.emp_table.setItem(i, 3, QTableWidgetItem(e.hire_date.strftime("%Y-%m-%d")))
            self.emp_table.setItem(i, 4, QTableWidgetItem(str(e.salary_rate)))
            self.emp_table.setItem(i, 5, QTableWidgetItem(str(e.base_salary)))

    def _delete_employee(self):
        row = self.emp_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Ошибка", "Сначала выберите сотрудника")
            return
        emp_id = int(self.emp_table.item(row, 0).text())
        if QMessageBox.question(self, "Подтвердить удаление",
                                f"Удалить сотрудника ID={emp_id}?") == QMessageBox.Yes:
            self.manager.delete(emp_id)
            self._refresh_employees()

    def _handle_add_employee(self):
        if self.manager.add_employee_dialog(self):
            self._refresh_employees()

    # ————————— Таблица «Расчёт» —————————————————————————————————
    def _create_salary_tab(self) -> QWidget:
        w    = QWidget()
        vlay = QVBoxLayout(w)
        hlay = QHBoxLayout()

        btn_calc_sel = QPushButton("Рассчитать выделенные")
        btn_calc_sel.clicked.connect(self._calculate_selected)
        btn_calc_all = QPushButton("Рассчитать для всех")
        btn_calc_all.clicked.connect(self._calculate_all)
        btn_export   = QPushButton("Экспорт в Excel")
        btn_export.clicked.connect(self._export_excel)

        for btn in (btn_calc_sel, btn_calc_all, btn_export):
            hlay.addWidget(btn)
        hlay.addStretch()
        vlay.addLayout(hlay)

        self.salary_table = QTableWidget()
        self._setup_table(self.salary_table, [
            "ID", "ФИО", "Месяц", "Премии", "Начислено", "НДФЛ", "К выплате"
        ])
        vlay.addWidget(self.salary_table)
        self._refresh_salary_table()

        return w

    def _refresh_salary_table(self):
        month = self.calculator.current_month()
        emps = self.db.query(Employee).all()
        records = []
        for emp in emps:
            sal = (self.db.query(Salary)
                   .filter_by(employee_id=emp.id, month=month)
                   .first())
            if not sal:
                from database.models import Salary as SM
                sal = SM(
                    employee_id=emp.id, month=month,
                    bonus=0.0, overtime_sum=0.0,
                    gross=emp.base_salary, ndfl=0.0,
                    payout=0.0, company_costs=0.0
                )
                self.db.add(sal)
                self.db.commit()
            records.append((emp, sal))

        self.salary_table.setRowCount(len(records))
        for i, (emp, s) in enumerate(records):
            for col, txt in enumerate([emp.id, emp.full_name, s.month]):
                item = QTableWidgetItem(str(txt))
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self.salary_table.setItem(i, col, item)
            self.salary_table.setItem(i, 3, QTableWidgetItem(str(s.bonus)))
            self.salary_table.setItem(i, 4, QTableWidgetItem(str(s.gross)))
            for col, val in ((5, s.ndfl), (6, s.payout)):
                itm = QTableWidgetItem(str(val))
                itm.setFlags(itm.flags() & ~Qt.ItemIsEditable)
                self.salary_table.setItem(i, col, itm)

    def _calculate_selected(self):
        month = self.calculator.current_month()
        rows = {idx.row() for idx in self.salary_table.selectedIndexes()}
        if not rows:
            QMessageBox.information(self, "Внимание", "Выберите строки для расчёта")
            return
        for r in rows:
            emp_id = int(self.salary_table.item(r, 0).text())
            bonus = float(self.salary_table.item(r, 3).text())
            gross = float(self.salary_table.item(r, 4).text())
            rec = (self.db.query(Salary)
                   .filter_by(employee_id=emp_id, month=month)
                   .first())
            rec.bonus = bonus
            rec.gross = gross
            self.db.add(ActionLog(
                user_id=self.user.id,
                action="edit_salary",
                details=f"{emp_id},{month},{bonus},{gross}"
            ))
            self.db.commit()
        self.calculator.compute_month(month)
        self._refresh_salary_table()
        QMessageBox.information(self, "Готово", "Пересчёт завершён")

    def _calculate_all(self):
        month = self.calculator.current_month()
        self.calculator.compute_month(month)
        self.db.add(ActionLog(
            user_id=self.user.id,
            action="calc_all",
            details=month
        ))
        self.db.commit()
        self._refresh_salary_table()
        QMessageBox.information(self, "Готово", "Массовый пересчёт завершён")

    def _export_excel(self):
        month = self.calculator.current_month()
        path = self.exporter.export_salary_report(month)
        QMessageBox.information(self, "Экспорт", f"Сохранено: {path}")
        self.db.add(ActionLog(
            user_id=self.user.id,
            action="export_excel",
            details=month
        ))
        self.db.commit()

    # ————————— Вкладка «Бонусы» ——————————————————————————————————
    def _create_bonus_tab(self) -> QWidget:
        w    = QWidget()
        vlay = QVBoxLayout(w)
        form = QFormLayout()
        self.b_emp_cb    = QComboBox()
        for e in self.db.query(Employee).all():
            self.b_emp_cb.addItem(f"{e.id} {e.full_name}", e.id)
        self.b_month_le  = QLineEdit(datetime.now().strftime("%m.%Y"))
        self.b_amount_le = QLineEdit()
        form.addRow("Сотрудник:", self.b_emp_cb)
        form.addRow("Месяц:",      self.b_month_le)
        form.addRow("Сумма:",      self.b_amount_le)
        btn_add = QPushButton("Добавить")
        btn_add.clicked.connect(self._add_bonus)
        vlay.addLayout(form)
        vlay.addWidget(btn_add)

        self.bonus_table = QTableWidget()
        self._setup_table(self.bonus_table, ["ID", "Сотрудник", "Месяц", "Сумма"])
        vlay.addWidget(self.bonus_table)

        btn_del = QPushButton("Удалить")
        btn_del.clicked.connect(self._del_bonus)
        vlay.addWidget(btn_del)

        self._refresh_bonus()
        return w

    def _refresh_bonus(self):
        recs = self.db.query(Bonus).all()
        self.bonus_table.setRowCount(len(recs))
        for i, b in enumerate(recs):
            self.bonus_table.setItem(i, 0, QTableWidgetItem(str(b.id)))
            self.bonus_table.setItem(i, 1, QTableWidgetItem(b.employee.full_name))
            self.bonus_table.setItem(i, 2, QTableWidgetItem(b.month))
            self.bonus_table.setItem(i, 3, QTableWidgetItem(str(b.amount)))

    def _add_bonus(self):
        emp_id = self.b_emp_cb.currentData()
        month = self.b_month_le.text().strip()
        try:
            amt = float(self.b_amount_le.text())
        except ValueError:
            QMessageBox.warning(self, "Ошибка", "Неверная сумма")
            return
        b = Bonus(employee_id=emp_id, month=month, amount=amt)
        self.db.add(b)
        self.db.add(ActionLog(
            user_id=self.user.id,
            action="add_bonus",
            details=f"{emp_id},{month},{amt}"
        ))
        self.db.commit()
        self._refresh_bonus()

    def _del_bonus(self):
        row = self.bonus_table.currentRow()
        if row < 0:
            return
        bid = int(self.bonus_table.item(row, 0).text())
        self.db.query(Bonus).filter_by(id=bid).delete()
        self.db.add(ActionLog(
            user_id=self.user.id,
            action="del_bonus",
            details=str(bid)
        ))
        self.db.commit()
        self._refresh_bonus()

    # ————————— Вкладка «Переработки» ——————————————————————————————
    def _create_overtime_tab(self) -> QWidget:
        w    = QWidget()
        vlay = QVBoxLayout(w)
        form = QFormLayout()
        self.o_emp_cb    = QComboBox()
        for e in self.db.query(Employee).all():
            self.o_emp_cb.addItem(f"{e.id} {e.full_name}", e.id)
        self.o_date_le   = QLineEdit(datetime.now().strftime("%Y-%m-%d"))
        self.o_hours_le  = QLineEdit()
        form.addRow("Сотрудник:", self.o_emp_cb)
        form.addRow("Дата:",       self.o_date_le)
        form.addRow("Часы:",       self.o_hours_le)
        btn_add = QPushButton("Добавить")
        btn_add.clicked.connect(self._add_overtime)
        vlay.addLayout(form)
        vlay.addWidget(btn_add)

        self.ot_table = QTableWidget()
        self._setup_table(self.ot_table, ["ID", "Сотрудник", "Дата", "Часы", "Множитель"])
        vlay.addWidget(self.ot_table)

        btn_del = QPushButton("Удалить")
        btn_del.clicked.connect(self._del_overtime)
        vlay.addWidget(btn_del)

        self._refresh_overtime()
        return w

    def _refresh_overtime(self):
        recs = self.db.query(Overtime).all()
        self.ot_table.setRowCount(len(recs))
        for i, o in enumerate(recs):
            self.ot_table.setItem(i, 0, QTableWidgetItem(str(o.id)))
            self.ot_table.setItem(i, 1, QTableWidgetItem(o.employee.full_name))
            self.ot_table.setItem(i, 2, QTableWidgetItem(o.date.strftime("%Y-%m-%d")))
            self.ot_table.setItem(i, 3, QTableWidgetItem(str(o.hours)))
            self.ot_table.setItem(i, 4, QTableWidgetItem(str(o.multiplier)))

    def _add_overtime(self):
        emp_id = self.o_emp_cb.currentData()
        date_s = self.o_date_le.text().strip()
        try:
            dt = datetime.strptime(date_s, "%Y-%m-%d").date()
            hrs = float(self.o_hours_le.text())
        except Exception:
            QMessageBox.warning(self, "Ошибка", "Неверный ввод")
            return
        ot = Overtime(employee_id=emp_id, date=dt, hours=hrs)
        self.db.add(ot)
        self.db.add(ActionLog(
            user_id=self.user.id,
            action="add_overtime",
            details=f"{emp_id},{date_s},{hrs}"
        ))
        self.db.commit()
        self._refresh_overtime()

    def _del_overtime(self):
        row = self.ot_table.currentRow()
        if row < 0:
            return
        oid = int(self.ot_table.item(row, 0).text())
        self.db.query(Overtime).filter_by(id=oid).delete()
        self.db.add(ActionLog(
            user_id=self.user.id,
            action="del_overtime",
            details=str(oid)
        ))
        self.db.commit()
        self._refresh_overtime()

    # ————————— Вкладка «Отчёты» ——————————————————————————————————
    def _create_report_tab(self) -> QWidget:
        w    = QWidget()
        vlay = QVBoxLayout(w)

        self.report_month = QLineEdit(datetime.now().strftime("%m.%Y"))
        vlay.addWidget(QLabel("Период (MM.YYYY):"))
        vlay.addWidget(self.report_month)

        btn_funds = QPushButton("Отчёт по фондам")
        btn_funds.clicked.connect(self._show_funds_report)
        vlay.addWidget(btn_funds)

        btn_dash = QPushButton("Показать дашборд")
        btn_dash.clicked.connect(self._show_dashboard)
        vlay.addWidget(btn_dash)

        self.log_table = QTableWidget()
        self._setup_table(self.log_table, ["ID", "Пользователь", "Действие", "Время"])
        vlay.addWidget(self.log_table)
        self._refresh_logs()

        return w

    def _show_funds_report(self):
        month = self.report_month.text().strip()
        recs  = self.db.query(Salary).filter(Salary.month == month).all()
        total = sum(r.gross for r in recs)
        pfr   = round(total * SalaryCalculator.CONTRIBUTION_PFR, 2)
        foms  = round(total * SalaryCalculator.CONTRIBUTION_FOMS, 2)
        fss   = round(total * SalaryCalculator.CONTRIBUTION_FSS, 2)
        msg = (
            f"За {month}:\n"
            f"Начислено: {total}\n"
            f"ПФР (22%): {pfr}\n"
            f"ФОМС (5.1%): {foms}\n"
            f"ФСС (2.9%): {fss}"
        )
        QMessageBox.information(self, "Отчёт по фондам", msg)
        self.db.add(ActionLog(
            user_id=self.user.id,
            action="view_funds_report",
            details=month
        ))
        self.db.commit()

    def _show_dashboard(self):
        month = self.report_month.text().strip()
        recs  = (
            self.db.query(Salary)
                   .join(Employee)
                   .options(joinedload(Salary.employee))
                   .filter(Salary.month == month)
                   .all()
        )
        xs    = [r.employee.full_name for r in recs]
        ys1   = [r.gross for r in recs]
        ys2   = [r.payout for r in recs]

        plt.figure()
        plt.plot(xs, ys1, label="Начислено (gross)")
        plt.plot(xs, ys2, label="К выплате (payout)")
        plt.title(f"Dashboard за {month}")
        plt.xlabel("Сотрудник")
        plt.ylabel("Сумма, руб.")
        plt.xticks(rotation=45, ha="right")
        plt.legend()
        plt.tight_layout()
        plt.show()

        self.db.add(ActionLog(
            user_id=self.user.id,
            action="view_dashboard",
            details=month
        ))
        self.db.commit()

    def _refresh_logs(self):
        logs = (self.db.query(ActionLog)
                .order_by(ActionLog.ts.desc())
                .limit(50)
                .all())
        self.log_table.setRowCount(len(logs))
        for i, lg in enumerate(logs):
            self.log_table.setItem(i, 0, QTableWidgetItem(str(lg.id)))
            self.log_table.setItem(i, 1, QTableWidgetItem(
                lg.user.full_name if lg.user else "—"))
            self.log_table.setItem(i, 2, QTableWidgetItem(lg.action))
            self.log_table.setItem(i, 3, QTableWidgetItem(
                lg.ts.strftime("%Y-%m-%d %H:%M:%S")))

    # ————————— Вкладка «Сообщения» —————————————————————————————————
    def _create_messages_tab(self) -> QWidget:
        w    = QWidget()
        vlay = QVBoxLayout(w)

        self.msg_table = QTableWidget()
        self._setup_table(self.msg_table, ["ID", "От кого", "Текст", "Время", "Прочитано"])
        vlay.addWidget(self.msg_table)

        hl = QHBoxLayout()
        btn_refresh = QPushButton("Обновить")
        btn_refresh.clicked.connect(self._refresh_messages)
        btn_mark    = QPushButton("Отметить прочитано")
        btn_mark.clicked.connect(self._mark_read)
        btn_reply   = QPushButton("Ответить")
        btn_reply.clicked.connect(self._reply_message)
        hl.addWidget(btn_refresh)
        hl.addWidget(btn_mark)
        hl.addWidget(btn_reply)
        hl.addStretch()
        vlay.addLayout(hl)

        vlay.addWidget(QLabel("Текст ответа:"))
        self.reply_edit = QTextEdit()
        vlay.addWidget(self.reply_edit)

        self._refresh_messages()
        return w

    def _refresh_messages(self):
        recs = (self.db.query(SupportMessage)
                .filter(SupportMessage.to_user_id == self.user.id)
                .order_by(SupportMessage.ts.desc())
                .all())
        self.msg_table.setRowCount(len(recs))
        for i, m in enumerate(recs):
            self.msg_table.setItem(i, 0, QTableWidgetItem(str(m.id)))
            self.msg_table.setItem(i, 1, QTableWidgetItem(m.sender.full_name))
            self.msg_table.setItem(i, 2, QTableWidgetItem(m.text))
            self.msg_table.setItem(i, 3, QTableWidgetItem(m.ts.strftime("%Y-%m-%d %H:%M")))
            chk = "Да" if m.is_read else "Нет"
            self.msg_table.setItem(i, 4, QTableWidgetItem(chk))

    def _mark_read(self):
        for idx in self.msg_table.selectionModel().selectedRows():
            msg_id = int(self.msg_table.item(idx.row(), 0).text())
            m = self.db.query(SupportMessage).get(msg_id)
            if m and not m.is_read:
                m.is_read = True
                self.db.add(m)
        self.db.commit()
        self._refresh_messages()

    def _reply_message(self):
        sel = self.msg_table.selectionModel().selectedRows()
        if not sel:
            QMessageBox.warning(self, "Ошибка", "Сначала выберите сообщение")
            return
        msg_id = int(self.msg_table.item(sel[0].row(), 0).text())
        orig = self.db.query(SupportMessage).get(msg_id)
        if not orig:
            QMessageBox.warning(self, "Ошибка", "Сообщение не найдено")
            return
        reply_text = self.reply_edit.toPlainText().strip()
        if not reply_text:
            QMessageBox.warning(self, "Ошибка", "Введите текст ответа")
            return
        resp = SupportMessage(
            from_user_id=self.user.id,
            to_user_id=orig.from_user_id,
            text=reply_text,
            is_read=False
        )
        self.db.add(resp)
        orig.is_read = True
        self.db.add(orig)
        self.db.commit()
        self.reply_edit.clear()
        self._refresh_messages()
        QMessageBox.information(self, "Успех", "Ответ отправлен")
