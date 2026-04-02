"""
Écran d'authentification — connexion et création de compte.
"""

import customtkinter as ctk
from core import config as cfg
from core.database import authenticate_user, create_user


class AuthScreen(ctk.CTkFrame):
    """Écran de login/register affiché au démarrage."""

    def __init__(self, master, on_login):
        super().__init__(master, fg_color=cfg.COLORS["bg_dark"])
        self.on_login = on_login
        self._mode = "login"  # "login" | "register"
        self._build()

    def _build(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        # Centre card
        card = ctk.CTkFrame(self, fg_color=cfg.COLORS["bg_panel"],
                            corner_radius=16, border_width=1,
                            border_color=cfg.COLORS["border"])
        card.grid(row=0, column=0)
        card.columnconfigure(0, weight=1)

        # ASCII logo
        logo = ctk.CTkLabel(card, text="[LaTaverneAI]",
                            font=cfg.FONTS["title"],
                            text_color=cfg.COLORS["accent"])
        logo.grid(row=0, column=0, padx=48, pady=(40, 4))

        self._subtitle = ctk.CTkLabel(card, text="// connexion",
                                      font=cfg.FONTS["small"],
                                      text_color=cfg.COLORS["text_dim"])
        self._subtitle.grid(row=1, column=0, padx=48, pady=(0, 28))

        # Champs
        self._username = ctk.CTkEntry(card, placeholder_text="identifiant",
                                      width=280, height=40,
                                      font=cfg.FONTS["body"],
                                      fg_color=cfg.COLORS["bg_card"],
                                      border_color=cfg.COLORS["border"],
                                      text_color=cfg.COLORS["text_primary"])
        self._username.grid(row=2, column=0, padx=48, pady=6)

        self._password = ctk.CTkEntry(card, placeholder_text="mot de passe",
                                      show="●", width=280, height=40,
                                      font=cfg.FONTS["body"],
                                      fg_color=cfg.COLORS["bg_card"],
                                      border_color=cfg.COLORS["border"],
                                      text_color=cfg.COLORS["text_primary"])
        self._password.grid(row=3, column=0, padx=48, pady=6)
        self._password.bind("<Return>", lambda e: self._submit())

        # Confirm password (register only)
        self._confirm = ctk.CTkEntry(card, placeholder_text="confirmer le mot de passe",
                                     show="●", width=280, height=40,
                                     font=cfg.FONTS["body"],
                                     fg_color=cfg.COLORS["bg_card"],
                                     border_color=cfg.COLORS["border"],
                                     text_color=cfg.COLORS["text_primary"])
        self._confirm.grid(row=4, column=0, padx=48, pady=6)
        self._confirm.grid_remove()
        self._confirm.bind("<Return>", lambda e: self._submit())

        # Error label
        self._error = ctk.CTkLabel(card, text="", font=cfg.FONTS["small"],
                                   text_color=cfg.COLORS["danger"])
        self._error.grid(row=5, column=0, padx=48, pady=(4, 0))

        # Submit button
        self._submit_btn = ctk.CTkButton(
            card, text="CONNEXION", width=280, height=42,
            font=cfg.FONTS["heading"],
            fg_color=cfg.COLORS["accent"], hover_color=cfg.COLORS["accent_dim"],
            text_color="#0A0E1A", corner_radius=8,
            command=self._submit
        )
        self._submit_btn.grid(row=6, column=0, padx=48, pady=(20, 8))

        # Toggle mode
        self._toggle_btn = ctk.CTkButton(
            card, text="Créer un compte →",
            font=cfg.FONTS["small"], width=280, height=32,
            fg_color="transparent", hover_color=cfg.COLORS["bg_card"],
            text_color=cfg.COLORS["text_dim"],
            command=self._toggle_mode
        )
        self._toggle_btn.grid(row=7, column=0, padx=48, pady=(0, 32))

        # Guest button
        guest_btn = ctk.CTkButton(
            card, text="continuer sans compte",
            font=cfg.FONTS["small"], width=280, height=28,
            fg_color="transparent", hover_color="#333333",
            text_color=cfg.COLORS["text_dim"],
            command=lambda: self.on_login({"id": 0, "username": "Invité", "settings": {}}, guest=True)
        )
        guest_btn.grid(row=8, column=0, padx=48, pady=(0, 32))

    def _toggle_mode(self):
        if self._mode == "login":
            self._mode = "register"
            self._subtitle.configure(text="// créer un compte")
            self._submit_btn.configure(text="CRÉER LE COMPTE")
            self._toggle_btn.configure(text="← Déjà un compte ?")
            self._confirm.grid()
        else:
            self._mode = "login"
            self._subtitle.configure(text="// connexion")
            self._submit_btn.configure(text="CONNEXION")
            self._toggle_btn.configure(text="Créer un compte →")
            self._confirm.grid_remove()
        self._error.configure(text="")

    def _submit(self):
        username = self._username.get().strip()
        password = self._password.get()
        self._error.configure(text="")

        if not username or not password:
            self._error.configure(text="Remplissez tous les champs.")
            return

        if self._mode == "register":
            confirm = self._confirm.get()
            if password != confirm:
                self._error.configure(text="Les mots de passe ne correspondent pas.")
                return
            if len(password) < 4:
                self._error.configure(text="Mot de passe trop court (min 4 caractères).")
                return
            user = create_user(username, password)
            if not user:
                self._error.configure(text="Ce nom d'utilisateur est déjà pris.")
                return
            self.on_login(user)
        else:
            user = authenticate_user(username, password)
            if not user:
                self._error.configure(text="Identifiants incorrects.")
                return
            self.on_login(user)
