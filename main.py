# main.py
import sys
from PyQt5.QtWidgets import QApplication, QDialog
from config import init_db, apply_theme
from auth.login_window import LoginWindow
from employee.employee_window import EmployeeWindow
from admin.admin_window import AdminWindow

def main():
    # Инициализируем БД (создаёт файлы и таблицы, если нужно)
    init_db()

    app = QApplication(sys.argv)
    apply_theme(app)  # светлая/тёмная тема из qt-material

    # Окно логина
    login_dialog = LoginWindow()
    if login_dialog.exec_() == QDialog.Accepted:
        user = login_dialog.current_user
        # В зависимости от роли открываем нужный интерфейс
        if user.position.lower() in ("бухгалтер", "admin", "accountant"):
            window = AdminWindow(user)
        else:
            window = EmployeeWindow(user)
        window.show()
        sys.exit(app.exec_())
    else:
        # Пользователь не залогинился или закрыл окно
        sys.exit(0)

if __name__ == "__main__":
    main()
