# employee/employee_window.py

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTableWidget, QTableWidgetItem,
    QLabel, QComboBox, QTextEdit, QFileDialog,
    QLineEdit, QTabWidget, QMessageBox, QHeaderView
)
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt, pyqtSignal
from database.db_init import SessionLocal
from database.models import Salary, SupportMessage, Employee
from employee.payslip_generator import PayslipGenerator
from datetime import datetime
import os

class EmployeeWindow(QMainWindow):
    # Сигнал для смены пользователя
    logout_requested = pyqtSignal()

    def __init__(self, user):
        super().__init__()
        self.user = user
        self.db   = SessionLocal()
        self.generator = PayslipGenerator()
        self.setWindowTitle(f"Личный кабинет — {user.full_name}")
        self.resize(1024, 640)

        # При логауте закрываем окно
        self.logout_requested.connect(self.close)

        # Кнопка «Сменить пользователя»
        btn_logout = QPushButton("Сменить пользователя")
        btn_logout.clicked.connect(self._on_logout)

        # Табуляция
        tabs = QTabWidget()
        tabs.addTab(self._create_salary_tab(),  "Моя зарплата")
        tabs.addTab(self._create_profile_tab(), "Профиль")

        # Сборка layout
        central = QWidget()
        lay = QVBoxLayout(central)
        # верхняя панель с кнопкой logout
        top_h = QHBoxLayout()
        top_h.addStretch()
        top_h.addWidget(btn_logout)
        lay.addLayout(top_h)
        # затем сами вкладки
        lay.addWidget(tabs)
        self.setCentralWidget(central)

    def _on_logout(self):
        """Эмитируем сигнал смены пользователя — закроется окно."""
        self.logout_requested.emit()

    def _create_salary_tab(self) -> QWidget:
        w    = QWidget()
        vlay = QVBoxLayout(w)
        hlay = QHBoxLayout()

        hlay.addWidget(QLabel("Месяц:"))
        self.month_cb = QComboBox()
        now = datetime.now()
        for i in range(12):
            m = (now.month - i - 1) % 12 + 1
            y = now.year - ((now.month - i - 1) // 12)
            self.month_cb.addItem(f"{m:02d}.{y}")
        hlay.addWidget(self.month_cb)

        btn_load = QPushButton("Показать")
        btn_load.clicked.connect(self.load_data)
        hlay.addWidget(btn_load)
        vlay.addLayout(hlay)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels([
            "ID", "Премии", "Начислено", "НДФЛ", "К выплате"
        ])
        hdr = self.table.horizontalHeader()
        hdr.setSectionResizeMode(QHeaderView.Stretch)
        self.table.setEditTriggers(self.table.NoEditTriggers)
        vlay.addWidget(self.table)

        btns = QHBoxLayout()
        btn_pdf   = QPushButton("Скачать PDF")
        btn_excel = QPushButton("Скачать Excel")
        btn_pdf.clicked.connect(lambda: self.export("pdf"))
        btn_excel.clicked.connect(lambda: self.export("xlsx"))
        btns.addStretch()
        btns.addWidget(btn_pdf)
        btns.addWidget(btn_excel)
        vlay.addLayout(btns)

        return w

    def load_data(self):
        month = self.month_cb.currentText()
        rec = (
            self.db.query(Salary)
            .filter(Salary.employee_id == self.user.id, Salary.month == month)
            .first()
        )
        self.table.setRowCount(1 if rec else 0)
        if rec:
            self.table.setItem(0, 0, QTableWidgetItem(str(rec.id)))
            self.table.setItem(0, 1, QTableWidgetItem(str(rec.bonus)))
            self.table.setItem(0, 2, QTableWidgetItem(str(rec.gross)))
            self.table.setItem(0, 3, QTableWidgetItem(str(rec.ndfl)))
            self.table.setItem(0, 4, QTableWidgetItem(str(rec.payout)))

    def export(self, fmt: str):
        month = self.month_cb.currentText()
        rec = (
            self.db.query(Salary)
            .filter(Salary.employee_id == self.user.id, Salary.month == month)
            .first()
        )
        if not rec:
            QMessageBox.warning(self, "Ошибка", "Нет данных для экспорта")
            return
        if fmt == "pdf":
            self.generator.generate_pdf(self.user, rec)
        else:
            self.generator.generate_excel(self.user, rec)
        QMessageBox.information(self, "Готово", f"Расчётный лист сохранён ({fmt})")

    def _create_profile_tab(self) -> QWidget:
        w = QWidget()
        vlay = QVBoxLayout(w)

        # Аватар
        self.avatar_lbl = QLabel()
        avatar_dir = os.path.join(os.getcwd(), "avatars")
        os.makedirs(avatar_dir, exist_ok=True)
        self.avatar_path = os.path.join(avatar_dir, f"{self.user.id}.png")
        if os.path.exists(self.avatar_path):
            pix = QPixmap(self.avatar_path).scaled(100,100, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.avatar_lbl.setPixmap(pix)
        else:
            self.avatar_lbl.setText("[Нет фото]")
            self.avatar_lbl.setFixedSize(100,100)
            self.avatar_lbl.setStyleSheet("border:1px solid #888;")
        btn_change = QPushButton("Изменить фото")
        btn_change.clicked.connect(self._change_avatar)
        vlay.addWidget(self.avatar_lbl, alignment=Qt.AlignCenter)
        vlay.addWidget(btn_change, alignment=Qt.AlignCenter)

        # Личные данные
        vlay.addWidget(QLabel(f"ФИО: {self.user.full_name}"))
        vlay.addWidget(QLabel(f"Должность: {self.user.position}"))
        vlay.addSpacing(15)

        # Отправка сообщения бухгалтеру
        self.buhgalters = (
            self.db.query(Employee)
            .filter(Employee.position.ilike("%бухгалтер%"))
            .all()
        )
        vlay.addWidget(QLabel("Выберите бухгалтера:"))
        self.buhgalter_cb = QComboBox()
        for b in self.buhgalters:
            self.buhgalter_cb.addItem(b.full_name, userData=b.id)
        vlay.addWidget(self.buhgalter_cb)

        vlay.addWidget(QLabel("Сообщение бухгалтеру:"))
        self.msg_edit = QTextEdit()
        vlay.addWidget(self.msg_edit)

        btn_send = QPushButton("Отправить")
        btn_send.clicked.connect(self._send_message)
        vlay.addWidget(btn_send, alignment=Qt.AlignRight)
        vlay.addSpacing(20)

        # История переписки
        vlay.addWidget(QLabel("История переписки:"))
        self.chat_table = QTableWidget(0, 4)
        self.chat_table.setHorizontalHeaderLabels(
            ["От кого", "Кому", "Текст", "Время"]
        )
        chat_hdr = self.chat_table.horizontalHeader()
        chat_hdr.setSectionResizeMode(QHeaderView.Stretch)
        self.chat_table.setWordWrap(True)
        vlay.addWidget(self.chat_table)
        self._refresh_chat()

        return w

    def _change_avatar(self):
        path, _ = QFileDialog.getOpenFileName(self, "Выберите фото", "", "Images (*.png *.jpg)")
        if not path:
            return
        pix = QPixmap(path).scaled(100,100, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        pix.save(self.avatar_path, "PNG")
        self.avatar_lbl.setPixmap(pix)

    def _send_message(self):
        text = self.msg_edit.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, "Ошибка", "Введите сообщение")
            return
        admin_id = self.buhgalter_cb.currentData()
        admin = self.db.query(Employee).get(admin_id)
        if not admin:
            QMessageBox.warning(self, "Ошибка", "Бухгалтер не выбран")
            return
        msg = SupportMessage(
            from_user_id=self.user.id,
            to_user_id=admin.id,
            text=text,
            is_read=False
        )
        self.db.add(msg)
        self.db.commit()
        self.msg_edit.clear()
        QMessageBox.information(self, "Готово", "Сообщение отправлено")
        self._refresh_chat()

    def _refresh_chat(self):
        admin_id = self.buhgalter_cb.currentData()
        admin = self.db.query(Employee).get(admin_id)
        if not admin:
            return
        msgs = (
            self.db.query(SupportMessage)
            .filter(
                ((SupportMessage.from_user_id == self.user.id) &
                 (SupportMessage.to_user_id   == admin.id))
                |
                ((SupportMessage.from_user_id == admin.id) &
                 (SupportMessage.to_user_id   == self.user.id))
            )
            .order_by(SupportMessage.ts.asc())
            .all()
        )
        self.chat_table.setRowCount(len(msgs))
        for i, m in enumerate(msgs):
            self.chat_table.setItem(i, 0, QTableWidgetItem(m.sender.full_name))
            self.chat_table.setItem(i, 1, QTableWidgetItem(m.receiver.full_name))
            self.chat_table.setItem(i, 2, QTableWidgetItem(m.text))
            self.chat_table.setItem(i, 3, QTableWidgetItem(m.ts.strftime("%Y-%m-%d %H:%M")))
