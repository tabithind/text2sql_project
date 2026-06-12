import json
import os

class LanguageManager:
    _instance = None
    _current_lang = 'fr'
    _translations = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LanguageManager, cls).__new__(cls)
        return cls._instance

    def set_language(self, lang: str):
        if lang not in ['fr', 'en']:
            return
        self._current_lang = lang
        self._load_translations()

    def get_language(self) -> str:
        return self._current_lang

    def _load_translations(self):
        import sys
        if hasattr(sys, '_MEIPASS'):
            filepath = os.path.join(sys._MEIPASS, "translations", f"{self._current_lang}.json")
        else:
            filepath = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "translations", f"{self._current_lang}.json")
            
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    self._translations = json.load(f)
            except Exception:
                self._translations = {}
        else:
            self._translations = {}

    def get(self, key: str, default: str = None) -> str:
        """Récupère une traduction. Supporte les clés imbriquées (e.g. 'ui.login.title')."""
        if not self._translations:
            self._load_translations()
            
        keys = key.split('.')
        val = self._translations
        try:
            for k in keys:
                val = val[k]
            return str(val)
        except (KeyError, TypeError):
            return default if default is not None else key
