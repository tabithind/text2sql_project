from PyQt6.QtWidgets import QApplication

class ThemeManager:
    _instance = None
    _current_theme = 'light'

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ThemeManager, cls).__new__(cls)
        return cls._instance

    def set_theme(self, theme: str):
        if theme not in ['light', 'dark']:
            return
        self._current_theme = theme
        self.apply_theme()

    def get_theme(self) -> str:
        return self._current_theme

    def toggle_theme(self):
        new_theme = 'dark' if self._current_theme == 'light' else 'light'
        self.set_theme(new_theme)

    def apply_theme(self):
        try:
            # We will read from styles/{theme}.qss later when UI is built.
            # This is a placeholder for the actual reading logic.
            with open(f"styles/{self._current_theme}.qss", "r") as f:
                qss = f.read()
            app = QApplication.instance()
            if app:
                app.setStyleSheet(qss)
        except Exception as e:
            # Silently pass if stylesheet doesn't exist yet
            pass
