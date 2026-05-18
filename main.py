import sys
import os
import logging

# CRITICAL: Force UTF-8 encoding for all I/O operations
os.environ['PYTHONIOENCODING'] = 'utf-8'
if sys.stdout.encoding != 'utf-8':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from PyQt6.QtWidgets import QApplication, QMessageBox

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    app = QApplication(sys.argv)
    
    # 1. Load config and environment
    from config.settings import settings
    if not settings.MASTER_ENCRYPTION_KEY_BYTES:
        QMessageBox.critical(None, "Configuration Error", "MASTER_ENCRYPTION_KEY is not set in the .env file.")
        sys.exit(1)
        
    # 2. Run Database Migrations
    from database.migrations import run_migrations
    try:
        run_migrations()
    except Exception as e:
        QMessageBox.critical(None, "Database Error", f"Impossible de se connecter à MySQL.\nVérifiez que XAMPP est lancé et que MySQL est démarré.\n\nDetails: {e}")
        sys.exit(1)

    # 3. Apply default theme and language
    from services.theme_manager import ThemeManager
    from services.language_manager import LanguageManager
    ThemeManager().set_theme('light')
    LanguageManager().set_language('fr')

    # 4. Main App Controller for routing
    from ui.login_window import LoginWindow
    from ui.admin_setup_window import AdminSetupWindow
    from ui.admin.admin_dashboard import AdminDashboard
    from ui.user.user_dashboard import UserDashboard

    class AppRouter:
        def __init__(self):
            self.current_window = None
            self.show_login()

        def show_login(self):
            if self.current_window:
                self.current_window.close()
            self.current_window = LoginWindow()
            self.current_window.login_success.connect(self._handle_login_success)
            self.current_window.switch_to_admin_setup.connect(self.show_admin_setup)
            self.current_window.resize(600, 500)
            self.current_window.show()

        def show_admin_setup(self):
            if self.current_window:
                self.current_window.close()
            self.current_window = AdminSetupWindow()
            self.current_window.setup_success.connect(self.show_login)
            self.current_window.back_to_login.connect(self.show_login)
            self.current_window.resize(600, 600)
            self.current_window.show()

        def _handle_login_success(self, role, data):
            if self.current_window:
                self.current_window.close()
                
            if role == 'admin':
                self.current_window = AdminDashboard(data)
            else:
                self.current_window = UserDashboard(data)
                
            self.current_window.logout_requested.connect(self.show_login)
            self.current_window.resize(1024, 768)
            self.current_window.show()

    router = AppRouter()
    
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
