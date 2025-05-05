# auth/login_window.py

from PyQt5.QtWidgets import (
    QDialog, QFormLayout, QLineEdit, QPushButton, QMessageBox
)
from auth.auth_service import AuthService
from auth.register_window import RegisterWindow

class LoginWindow(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Вход")
        self.service = AuthService()
        self.current_user = None   # ← здесь

        layout = QFormLayout(self)
        self.username_edit = QLineEdit()
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.Password)

        layout.addRow("Логин (username):", self.username_edit)
        layout.addRow("Пароль:",          self.password_edit)

        btn_login    = QPushButton("Войти")
        btn_register = QPushButton("Регистрация")
        btn_login.clicked.connect(self.login)
        btn_register.clicked.connect(self.open_register)

        layout.addRow(btn_login, btn_register)

    def login(self):
        username = self.username_edit.text().strip()
        password = self.password_edit.text()
        user = self.service.authenticate_user(username, password)
        if user:
            self.current_user = user    # ← запоминаем пользователя
            self.accept()
        else:
            QMessageBox.warning(self, "Ошибка", "Неверный логин или пароль")

    def open_register(self):
        dlg = RegisterWindow()
        if dlg.exec_():
            QMessageBox.information(self, "Успех", "Теперь войдите с новым логином")
