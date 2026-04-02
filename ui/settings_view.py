"""
Panneau de paramètres — apparence, compte, IA.
S'affiche comme un overlay modal dans la fenêtre principale.
"""

import customtkinter as ctk
from core import config as cfg
from core.config import DEFAULT_FONT
from core.settings import load_settings, save_settings
from core.database import update_username, update_password


class SettingsView(ctk.CTkToplevel):
    """Fenêtre modale de paramètres."""

    CATEGORIES = [
        {"id": "appearance", "label": "🎨  Apparence"},
        {"id": "account",    "label": "👤  Compte"},
        {"id": "ai",         "label": "🤖  Intelligence artificielle"},
    ]

    def __init__(self, master, user: dict, on_close=None):
        super().__init__(master)
        self.user = user
        self.on_close_cb = on_close
        self._settings = load_settings(user["id"])
        self._current_cat = "appearance"

        self.title("Paramètres")
        self.geometry("700x520")
        self.resizable(False, False)
        self.configure(fg_color=cfg.COLORS["bg_dark"])
        self.transient(master)
        self.grab_set()

        self.protocol("WM_DELETE_WINDOW", self._close)
        self._build()

    def _close(self):
        self.grab_release()
        if self.on_close_cb:
            self.on_close_cb()
        self.destroy()

    # ─── Layout ──────────────────────────────────────────────────────────────

    def _build(self):
        self.columnconfigure(0, weight=0)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        # Sidebar catégories
        nav = ctk.CTkFrame(self, fg_color=cfg.COLORS["bg_panel"],
                           corner_radius=0, width=200)
        nav.grid(row=0, column=0, sticky="nsew")
        nav.pack_propagate(False)

        ctk.CTkLabel(nav, text="Paramètres",
                     font=cfg.FONTS["heading"],
                     text_color=cfg.COLORS["accent"]
                     ).pack(padx=16, pady=(20, 16), anchor="w")

        self._cat_buttons = {}
        for cat in self.CATEGORIES:
            btn = ctk.CTkButton(
                nav, text=cat["label"],
                font=cfg.FONTS["small"],
                fg_color="transparent",
                hover_color=cfg.COLORS["bg_card"],
                text_color=cfg.COLORS["text_primary"],
                anchor="w", height=36, corner_radius=8,
                command=lambda c=cat["id"]: self._select_category(c)
            )
            btn.pack(fill="x", padx=8, pady=2)
            self._cat_buttons[cat["id"]] = btn

        # Content area
        self._content = ctk.CTkScrollableFrame(
            self, fg_color=cfg.COLORS["bg_dark"],
            scrollbar_button_color=cfg.COLORS["border"]
        )
        self._content.grid(row=0, column=1, sticky="nsew", padx=0, pady=0)
        self._content.columnconfigure(0, weight=1)

        self._select_category("appearance")

    def _select_category(self, cat_id: str):
        self._current_cat = cat_id
        # Highlight
        for cid, btn in self._cat_buttons.items():
            btn.configure(
                fg_color=cfg.COLORS["bg_card"] if cid == cat_id else "transparent",
                text_color=cfg.COLORS["accent"] if cid == cat_id else cfg.COLORS["text_primary"]
            )
        # Clear content
        for w in self._content.winfo_children():
            w.destroy()
        # Build content
        builder = {
            "appearance": self._build_appearance,
            "account": self._build_account,
            "ai": self._build_ai,
        }
        builder.get(cat_id, lambda: None)()

    # ─── Helpers ─────────────────────────────────────────────────────────────

    def _section_title(self, text: str):
        ctk.CTkLabel(self._content, text=text,
                     font=(DEFAULT_FONT, 15, "bold"),
                     text_color=cfg.COLORS["text_primary"]
                     ).pack(anchor="w", padx=24, pady=(20, 4))

    def _section_desc(self, text: str):
        ctk.CTkLabel(self._content, text=text,
                     font=cfg.FONTS["small"],
                     text_color=cfg.COLORS["text_dim"],
                     wraplength=420, justify="left"
                     ).pack(anchor="w", padx=24, pady=(0, 12))

    def _field_row(self, label: str, widget_factory):
        """Crée une ligne : label à gauche, widget à droite."""
        row = ctk.CTkFrame(self._content, fg_color="transparent")
        row.pack(fill="x", padx=24, pady=4)
        row.columnconfigure(1, weight=1)

        ctk.CTkLabel(row, text=label, font=cfg.FONTS["body"],
                     text_color=cfg.COLORS["text_secondary"]
                     ).grid(row=0, column=0, sticky="w", padx=(0, 16))

        widget = widget_factory(row)
        widget.grid(row=0, column=1, sticky="ew")
        return widget

    def _separator(self):
        ctk.CTkFrame(self._content, fg_color=cfg.COLORS["border"],
                     height=1, corner_radius=0).pack(fill="x", padx=24, pady=12)

    def _feedback(self, text: str, success: bool = True):
        color = cfg.COLORS["accent"] if success else cfg.COLORS["danger"]
        lbl = ctk.CTkLabel(self._content, text=text,
                           font=cfg.FONTS["small"], text_color=color)
        lbl.pack(anchor="w", padx=24, pady=(4, 0))
        self.after(3000, lbl.destroy)

    # ─── APPARENCE ───────────────────────────────────────────────────────────

    def _build_appearance(self):
        self._section_title("Apparence")
        self._section_desc("Personnalisez les couleurs et la police de l'interface.")

        ap = self._settings.get("appearance", {})

        # Couleur d'accent
        self._accent_entry = self._field_row(
            "Couleur d'accent (hex)",
            lambda p: ctk.CTkEntry(p, font=cfg.FONTS["body"],
                                   fg_color=cfg.COLORS["bg_card"],
                                   border_color=cfg.COLORS["border"],
                                   text_color=cfg.COLORS["text_primary"],
                                   height=34)
        )
        self._accent_entry.insert(0, ap.get("accent_color", "#00FF88"))

        # Couleur preview
        self._color_preview = ctk.CTkFrame(self._content,
                                            fg_color=ap.get("accent_color", "#00FF88"),
                                            height=8, corner_radius=4)
        self._color_preview.pack(fill="x", padx=24, pady=(2, 8))
        self._accent_entry.bind("<KeyRelease>", self._update_color_preview)

        self._separator()

        # Police
        self._font_entry = self._field_row(
            "Police de l'interface",
            lambda p: ctk.CTkEntry(p, font=cfg.FONTS["body"],
                                   fg_color=cfg.COLORS["bg_card"],
                                   border_color=cfg.COLORS["border"],
                                   text_color=cfg.COLORS["text_primary"],
                                   height=34)
        )
        self._font_entry.insert(0, ap.get("font_family", "Inter"))

        # Taille
        self._fontsize_entry = self._field_row(
            "Taille de police",
            lambda p: ctk.CTkEntry(p, font=cfg.FONTS["body"],
                                   fg_color=cfg.COLORS["bg_card"],
                                   border_color=cfg.COLORS["border"],
                                   text_color=cfg.COLORS["text_primary"],
                                   width=80, height=34)
        )
        self._fontsize_entry.insert(0, str(ap.get("font_size", 12)))

        self._separator()

        # Save
        ctk.CTkButton(
            self._content, text="Enregistrer l'apparence",
            font=cfg.FONTS["heading"], height=38,
            fg_color=cfg.COLORS["accent"], hover_color=cfg.COLORS["accent_dim"],
            text_color="#0A0E1A", corner_radius=8,
            command=self._save_appearance
        ).pack(padx=24, pady=(8, 20), anchor="w")

    def _update_color_preview(self, event=None):
        color = self._accent_entry.get().strip()
        if len(color) == 7 and color.startswith("#"):
            try:
                self._color_preview.configure(fg_color=color)
            except Exception:
                pass

    def _save_appearance(self):
        self._settings["appearance"] = {
            "accent_color": self._accent_entry.get().strip(),
            "font_family": self._font_entry.get().strip(),
            "font_size": int(self._fontsize_entry.get().strip() or 12),
        }
        save_settings(self.user["id"], self._settings)
        self._feedback("✓ Apparence enregistrée. Redémarrez pour appliquer.")

    # ─── COMPTE ──────────────────────────────────────────────────────────────

    def _build_account(self):
        self._section_title("Compte")
        self._section_desc(f"Connecté en tant que : {self.user['username']}")

        # Changer le nom d'utilisateur
        ctk.CTkLabel(self._content, text="Nouveau nom d'utilisateur",
                     font=cfg.FONTS["small"],
                     text_color=cfg.COLORS["text_dim"]
                     ).pack(anchor="w", padx=24, pady=(12, 4))

        self._new_username = ctk.CTkEntry(
            self._content, font=cfg.FONTS["body"],
            fg_color=cfg.COLORS["bg_card"],
            border_color=cfg.COLORS["border"],
            text_color=cfg.COLORS["text_primary"],
            height=34, placeholder_text="Nouveau nom..."
        )
        self._new_username.pack(fill="x", padx=24, pady=(0, 4))

        ctk.CTkButton(
            self._content, text="Changer le nom",
            font=cfg.FONTS["small"], height=32, width=160,
            fg_color=cfg.COLORS["bg_card"],
            hover_color=cfg.COLORS["border"],
            text_color=cfg.COLORS["text_primary"],
            corner_radius=8, command=self._change_username
        ).pack(anchor="w", padx=24, pady=(0, 8))

        self._separator()

        # Changer le mot de passe
        ctk.CTkLabel(self._content, text="Changer le mot de passe",
                     font=(DEFAULT_FONT, 13, "bold"),
                     text_color=cfg.COLORS["text_primary"]
                     ).pack(anchor="w", padx=24, pady=(8, 8))

        self._old_pw = ctk.CTkEntry(
            self._content, font=cfg.FONTS["body"],
            fg_color=cfg.COLORS["bg_card"],
            border_color=cfg.COLORS["border"],
            text_color=cfg.COLORS["text_primary"],
            height=34, show="●", placeholder_text="Mot de passe actuel"
        )
        self._old_pw.pack(fill="x", padx=24, pady=3)

        self._new_pw = ctk.CTkEntry(
            self._content, font=cfg.FONTS["body"],
            fg_color=cfg.COLORS["bg_card"],
            border_color=cfg.COLORS["border"],
            text_color=cfg.COLORS["text_primary"],
            height=34, show="●", placeholder_text="Nouveau mot de passe"
        )
        self._new_pw.pack(fill="x", padx=24, pady=3)

        self._confirm_pw = ctk.CTkEntry(
            self._content, font=cfg.FONTS["body"],
            fg_color=cfg.COLORS["bg_card"],
            border_color=cfg.COLORS["border"],
            text_color=cfg.COLORS["text_primary"],
            height=34, show="●", placeholder_text="Confirmer le nouveau"
        )
        self._confirm_pw.pack(fill="x", padx=24, pady=3)

        ctk.CTkButton(
            self._content, text="Changer le mot de passe",
            font=cfg.FONTS["small"], height=32, width=200,
            fg_color=cfg.COLORS["bg_card"],
            hover_color=cfg.COLORS["border"],
            text_color=cfg.COLORS["text_primary"],
            corner_radius=8, command=self._change_password
        ).pack(anchor="w", padx=24, pady=(8, 20))

    def _change_username(self):
        new = self._new_username.get().strip()
        if not new:
            self._feedback("Entrez un nom d'utilisateur.", False); return
        if len(new) < 2:
            self._feedback("Nom trop court (min 2 caractères).", False); return

        if update_username(self.user["id"], new):
            self.user["username"] = new
            self._feedback(f"✓ Nom changé en '{new}'.")
        else:
            self._feedback("Ce nom est déjà pris.", False)

    def _change_password(self):
        old = self._old_pw.get()
        new = self._new_pw.get()
        confirm = self._confirm_pw.get()

        if not old or not new:
            self._feedback("Remplissez tous les champs.", False); return
        if new != confirm:
            self._feedback("Les mots de passe ne correspondent pas.", False); return
        if len(new) < 4:
            self._feedback("Mot de passe trop court (min 4).", False); return

        if update_password(self.user["id"], old, new):
            self._feedback("✓ Mot de passe changé.")
            self._old_pw.delete(0, "end")
            self._new_pw.delete(0, "end")
            self._confirm_pw.delete(0, "end")
        else:
            self._feedback("Mot de passe actuel incorrect.", False)

    # ─── IA ──────────────────────────────────────────────────────────────────

    def _build_ai(self):
        self._section_title("Intelligence artificielle")
        self._section_desc(
            "Définissez des instructions générales que l'IA suivra "
            "dans toutes vos conversations."
        )

        ai = self._settings.get("ai", {})

        ctk.CTkLabel(self._content, text="Instructions système",
                     font=cfg.FONTS["small"],
                     text_color=cfg.COLORS["text_dim"]
                     ).pack(anchor="w", padx=24, pady=(8, 4))

        self._system_prompt = ctk.CTkTextbox(
            self._content, height=200, font=cfg.FONTS["body"],
            fg_color=cfg.COLORS["bg_card"],
            border_color=cfg.COLORS["border"], border_width=1,
            text_color=cfg.COLORS["text_primary"],
            corner_radius=8, wrap="word"
        )
        self._system_prompt.pack(fill="x", padx=24, pady=(0, 8))
        self._system_prompt.insert("1.0", ai.get("system_prompt", ""))

        ctk.CTkLabel(self._content,
                     text="Exemple : \"Réponds toujours en français. Sois concis.\"",
                     font=cfg.FONTS["small"],
                     text_color=cfg.COLORS["text_dim"]
                     ).pack(anchor="w", padx=24, pady=(0, 12))

        ctk.CTkButton(
            self._content, text="Enregistrer les instructions",
            font=cfg.FONTS["heading"], height=38,
            fg_color=cfg.COLORS["accent"], hover_color=cfg.COLORS["accent_dim"],
            text_color="#0A0E1A", corner_radius=8,
            command=self._save_ai
        ).pack(padx=24, pady=(4, 20), anchor="w")

    def _save_ai(self):
        prompt = self._system_prompt.get("1.0", "end").strip()
        self._settings["ai"] = {"system_prompt": prompt}
        save_settings(self.user["id"], self._settings)
        self._feedback("✓ Instructions IA enregistrées.")
