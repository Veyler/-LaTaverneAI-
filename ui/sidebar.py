"""
Sidebar — liste des conversations + bouton nouvelle conversation.
"""

import customtkinter as ctk
from core import config as cfg
from core.config import APP_VERSION
from core.database import (
    get_conversations, create_conversation, delete_conversation,
    rename_conversation
)
from core.config import AVAILABLE_MODELS, DEFAULT_FONT
from ui.settings_view import SettingsView


class Sidebar(ctk.CTkFrame):
    def __init__(self, master, user: dict, on_select, on_new, on_logout):
        super().__init__(master,
                         fg_color=cfg.COLORS["bg_panel"],
                         corner_radius=0, width=240,
                         border_width=0)
        self.user = user
        self.on_select = on_select
        self.on_new = on_new
        self.on_logout = on_logout
        self._conv_id = None
        self._buttons = {}
        self._build()
        self.refresh()

    def _build(self):
        self.pack_propagate(False)
        self.columnconfigure(0, weight=1)

        # Header
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=12, pady=(16, 8))

        ctk.CTkLabel(hdr, text="[LaTaverneAI]", font=cfg.FONTS["heading"],
                     text_color=cfg.COLORS["accent"]).pack(side="left")
        
        self._version_label = ctk.CTkLabel(
            hdr, text=APP_VERSION,
            font=cfg.FONTS["body"], text_color=cfg.COLORS["text_dim"]
        )
        self._version_label.pack()

        # User info
        user_frame = ctk.CTkFrame(self, fg_color=cfg.COLORS["bg_card"],
                                  corner_radius=8)
        user_frame.pack(fill="x", padx=10, pady=(0, 10))

        self._username_label = ctk.CTkLabel(
            user_frame, text=f"◉  {self.user['username']}",
            font=cfg.FONTS["small"],
            text_color=cfg.COLORS["text_dim"])
        self._username_label.pack(side="left", padx=10, pady=8)

        ctk.CTkButton(user_frame, text="↩", width=28, height=28,
                      font=cfg.FONTS["body"],
                      fg_color="transparent", hover_color=cfg.COLORS["bg_mid"],
                      text_color=cfg.COLORS["text_dim"],
                      command=self.on_logout).pack(side="right", padx=6)

        ctk.CTkButton(user_frame, text="⚙", width=28, height=28,
                      font=cfg.FONTS["body"],
                      fg_color="transparent", hover_color=cfg.COLORS["bg_mid"],
                      text_color=cfg.COLORS["text_dim"],
                      command=self._open_settings).pack(side="right", padx=0)

        # New conversation button
        ctk.CTkButton(self, text="+ Nouvelle conversation",
                      font=cfg.FONTS["small"],
                      fg_color=cfg.COLORS["accent"], hover_color=cfg.COLORS["accent_dim"],
                      text_color="#0A0E1A", height=36, corner_radius=8,
                      command=self.on_new).pack(fill="x", padx=10, pady=(0, 12))

        # Separator label
        ctk.CTkLabel(self, text="HISTORIQUE", font=(DEFAULT_FONT, 9, "bold"),
                     text_color=cfg.COLORS["text_dim"]).pack(anchor="w", padx=14, pady=(0, 4))

        # Scrollable list
        self._list = ctk.CTkScrollableFrame(self, fg_color="transparent",
                                            scrollbar_button_color=cfg.COLORS["border"])
        self._list.pack(fill="both", expand=True, padx=6)
        self._list.columnconfigure(0, weight=1)

    def refresh(self, select_id: int = None):
        """Recharge la liste des conversations."""
        for w in self._list.winfo_children():
            w.destroy()
        self._buttons.clear()

        if self.user["id"] == 0:
            ctk.CTkLabel(self._list, text="(mode invité\npas d'historique)",
                         font=cfg.FONTS["small"],
                         text_color=cfg.COLORS["text_dim"],
                         justify="center").pack(pady=20)
            return

        convs = get_conversations(self.user["id"])
        for conv in convs:
            self._add_conv_row(conv)

        if select_id:
            self._highlight(select_id)
        elif convs:
            self._highlight(convs[0]["id"])

    def _add_conv_row(self, conv: dict):
        row = ctk.CTkFrame(self._list, fg_color="transparent", corner_radius=6)
        row.pack(fill="x", pady=2)
        row.columnconfigure(0, weight=1)

        btn = ctk.CTkButton(
            row, text=conv["title"],
            font=cfg.FONTS["small"],
            fg_color="transparent",
            hover_color=cfg.COLORS["bg_card"],
            text_color=cfg.COLORS["text_primary"],
            anchor="w", height=34, corner_radius=6,
            command=lambda cid=conv["id"]: self._select(cid)
        )
        btn.grid(row=0, column=0, sticky="ew")

        del_btn = ctk.CTkButton(
            row, text="✕", width=24, height=24,
            font=(DEFAULT_FONT, 9),
            fg_color="transparent", hover_color=cfg.COLORS["danger"],
            text_color=cfg.COLORS["text_dim"],
            command=lambda cid=conv["id"], r=row: self._delete(cid, r)
        )
        del_btn.grid(row=0, column=1, padx=(0, 4))

        self._buttons[conv["id"]] = btn

    def _select(self, conv_id: int):
        self._highlight(conv_id)
        self.on_select(conv_id)

    def _highlight(self, conv_id: int):
        for cid, btn in self._buttons.items():
            btn.configure(
                fg_color=cfg.COLORS["bg_card"] if cid == conv_id else "transparent",
                text_color=cfg.COLORS["accent"] if cid == conv_id else cfg.COLORS["text_primary"]
            )
        self._conv_id = conv_id

    def _delete(self, conv_id: int, row_widget):
        delete_conversation(conv_id)
        row_widget.destroy()
        self._buttons.pop(conv_id, None)
        if self._conv_id == conv_id:
            self.on_new()

    def _open_settings(self):
        def on_close():
            # Rafraîchir le nom d'utilisateur si changé
            self._username_label.configure(text=f"◉  {self.user['username']}")

        SettingsView(self.winfo_toplevel(), self.user, on_close=on_close)
