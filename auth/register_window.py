# auth/register_window.py

from PyQt5.QtWidgets import QDialog, QFormLayout, QLineEdit, QPushButton, QMessageBox
from auth.auth_service import AuthService
from datetime import date

class RegisterWindow(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Регистрация")
        self.service = AuthService()

        form = QFormLayout(self)
        self.username_edit  = QLineEdit()                                  # Новый!
        self.full_name_edit = QLineEdit()
        self.position_edit  = QLineEdit()
        self.password_edit  = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.hire_date_edit = QLineEdit(date.today().strftime("%Y-%m-%d"))

        form.addRow("Логин (username):",     self.username_edit)
        form.addRow("ФИО (полное имя):",     self.full_name_edit)
        form.addRow("Должность:",            self.position_edit)
        form.addRow("Пароль:",               self.password_edit)
        form.addRow("Дата приёма (YYYY-MM-DD):", self.hire_date_edit)

        btn = QPushButton("Зарегистрироваться")
        btn.clicked.connect(self.register)
        form.addWidget(btn)

    def register(self):
        usr  = self.username_edit.text().strip()
        name = self.full_name_edit.text().strip()
        pos  = self.position_edit.text().strip()
        pwd  = self.password_edit.text()
        dt   = self.hire_date_edit.text().strip()
        ok, msg = self.service.register_user(usr, name, pos, pwd, dt)
        if ok:
            QMessageBox.information(self, "Успех", "Пользователь зарегистрирован")
            self.accept()
        else:
            QMessageBox.warning(self, "Ошибка", msg)
