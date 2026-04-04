"""
LaTaverneIA — Point d'entrée principal.

"""

import os
import sys
import customtkinter as ctk
from core.config import (
    APP_NAME, THEME, COLOR_THEME,
    WINDOW_START_WIDTH, WINDOW_START_HEIGHT,
    WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT,
    COLORS
)
from core.database import init_db
from core.settings import load_settings
from core import config as cfg
from ui.auth_screen import AuthScreen
from ui.sidebar import Sidebar
from ui.chat_view import ChatView
import threading
from ui.splash_screen import SplashScreen
from core.updater import check_for_updates, download_and_install_update


class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        ctk.set_appearance_mode(THEME)
        ctk.set_default_color_theme(COLOR_THEME)

        self.title(APP_NAME)
        self.geometry(f"{WINDOW_START_WIDTH}x{WINDOW_START_HEIGHT}")
        self.minsize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)
        self.configure(fg_color=COLORS["bg_dark"])

        # Set application icon
        try:
            base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
            icon_path = os.path.join(base_path, "icons", "icon128x128.ico")
            self.iconbitmap(icon_path)
        except Exception:
            pass

        self._user = None
        self._sidebar = None
        self._chat = None

        # Appliquer les paramètres du dernier utilisateur enregistré pour la fenêtre de connexion
        try:
            import sqlite3
            from core.config import DB_PATH
            with sqlite3.connect(DB_PATH) as conn:
                conn.row_factory = sqlite3.Row
                row = conn.execute("SELECT id FROM users ORDER BY id DESC LIMIT 1").fetchone()
            if row:
                self._apply_theme_for_user(row["id"])
        except Exception:
            pass

        # Hide main window initially
        self.withdraw()
        
        # Show splash screen
        self._splash = SplashScreen(self)
        self._splash.update()
        
        # Check updates in the background
        threading.Thread(target=self._check_updates, daemon=True).start()

    def _check_updates(self):
        self._splash.update_status("Recherche de mises à jour...")
        update_info = check_for_updates()
        if update_info:
            self._splash.update_status(f"Mise à jour {update_info['version']} trouvée...")
            download_and_install_update(update_info["url"], self._update_splash_callback)
        else:
            self._splash.update_status("Chargement de l'application...")
            self.after(500, self._finish_startup)
            
    def _update_splash_callback(self, text: str):
        # Utiliser after pour être thread-safe avec Tkinter
        self.after(0, lambda: self._splash.update_status(text))
        
    def _finish_startup(self):
        self._splash.destroy()
        self._show_auth()
        self.deiconify()

    # ─── Navigation ──────────────────────────────────────────────────────────

    def _clear(self):
        for w in self.winfo_children():
            w.destroy()

    def _show_auth(self):
        self._clear()
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        auth = AuthScreen(self, on_login=self._on_login)
        auth.grid(row=0, column=0, sticky="nsew")

    def _apply_theme_for_user(self, user_id: int):
        settings = load_settings(user_id)
        ap = settings.get("appearance", {})

        if "accent_color" in ap and ap["accent_color"]:
            accent = ap["accent_color"]
            cfg.COLORS["accent"] = accent
            
            def darken(hex_str, factor):
                try:
                    h = hex_str.lstrip('#')
                    r, g, b = tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
                    return f'#{int(r*factor):02x}{int(g*factor):02x}{int(b*factor):02x}'
                except:
                    return hex_str

            cfg.COLORS["accent_dim"] = darken(accent, 0.8)
            cfg.COLORS["h1"] = accent
            cfg.COLORS["h2"] = darken(accent, 0.9)
            cfg.COLORS["h3"] = darken(accent, 0.8)
            cfg.COLORS["list_bullet"] = accent

        if "font_family" in ap or "font_size" in ap:
            ff = ap.get("font_family", cfg.DEFAULT_FONT)
            try:
                fs = int(ap.get("font_size", 12))
            except ValueError:
                fs = 12
            cfg.FONTS["title"] = (ff, 22, "bold")
            cfg.FONTS["heading"] = (ff, 13, "bold")
            cfg.FONTS["body"] = (ff, fs)
            cfg.FONTS["small"] = (ff, max(9, fs - 2))

    def _on_login(self, user: dict, guest: bool = False):
        self._user = user
        if user["id"] != 0:
            self._apply_theme_for_user(user["id"])
        self._show_main()

    def _show_main(self):
        self._clear()
        self.columnconfigure(0, weight=0)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        self._sidebar = Sidebar(
            self,
            user=self._user,
            on_select=self._load_conv,
            on_new=self._new_conv,
            on_logout=self._logout
        )
        self._sidebar.grid(row=0, column=0, sticky="nsew")

        self._chat = ChatView(
            self,
            user=self._user,
            on_conv_created=self._on_conv_created
        )
        self._chat.grid(row=0, column=1, sticky="nsew")

        if self._user["id"] != 0:
            from core.database import get_conversations
            convs = get_conversations(self._user["id"])
            if convs:
                self._load_conv(convs[0]["id"])

    def _load_conv(self, conv_id: int):
        self._chat.load_conversation(conv_id)
        self._sidebar._highlight(conv_id)

    def _new_conv(self):
        self._chat.new_conversation()

    def _on_conv_created(self, conv_id: int):
        self._sidebar.refresh(select_id=conv_id)

    def _logout(self):
        self._user = None
        self._show_auth()


def main():
    init_db()
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
