# main.py
import sys
from PyQt5.QtWidgets import QApplication, QDialog
from config import init_db, apply_theme
from auth.login_window import LoginWindow
from employee.employee_window import EmployeeWindow
from admin.admin_window import AdminWindow

def main():
    init_db()
    app = QApplication(sys.argv)
    apply_theme(app)

    while True:
        # 1) Показываем диалог логина
        login_dialog = LoginWindow()
        if login_dialog.exec_() != QDialog.Accepted:
            # либо отмена, либо крестик — выходим из цикла
            break

        user = login_dialog.current_user
        # 2) В зависимости от роли создаём нужное окно
        if user.position.lower() in ("бухгалтер", "admin", "accountant"):
            window = AdminWindow(user)
        else:
            window = EmployeeWindow(user)

        # 3) Показываем окно, и ждём, пока оно закроется (в том числе по logout)
        window.show()
        app.exec_()

        # После закрытия окна (self.close()) мы снова окажемся в этом цикле
        # и покажем логин повторно.

    # Вышли из цикла — полностью завершаем приложение
    sys.exit(0)

if __name__ == "__main__":
    main()
