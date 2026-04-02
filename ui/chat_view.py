"""
Zone de chat principale : affichage des messages + zone de saisie.
"""

import threading
import tkinter as tk
import customtkinter as ctk

from core import config as cfg
from core.config import AVAILABLE_MODELS, DEFAULT_MODEL_ID, DEFAULT_FONT
from core.database import (
    create_conversation, get_messages, add_message,
    get_conversation_context, rename_conversation
)
from core.api_client import send_message, generate_title
from core.settings import load_settings
from ui.markdown_renderer import (
    create_markdown_text_widget,
    render_markdown_to_widget,
    animate_markdown_to_widget,
    auto_resize_text_widget,
)


def _model_label(model_id: str) -> str:
    for m in AVAILABLE_MODELS:
        if m["id"] == model_id:
            return m["label"]
    return model_id


class ChatView(ctk.CTkFrame):
    def __init__(self, master, user: dict, on_conv_created):
        super().__init__(master, fg_color=cfg.COLORS["bg_dark"], corner_radius=0)
        self.user = user
        self.on_conv_created = on_conv_created
        self._conv_id: int | None = None
        self._model_id = DEFAULT_MODEL_ID
        self._loading = False
        self._row = 1
        self._md_widgets = []
        self._build()
        self.bind("<Configure>", self._on_configure)

    def _build(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        self._build_topbar()
        self._build_msgarea()
        self._build_inputbar()

    def _build_topbar(self):
        bar = ctk.CTkFrame(self, fg_color=cfg.COLORS["bg_panel"],
                           corner_radius=0, height=48)
        bar.grid(row=0, column=0, sticky="ew")
        bar.columnconfigure(1, weight=1)
        bar.grid_propagate(False)

        self._model_var = ctk.StringVar(value=_model_label(self._model_id))
        ctk.CTkOptionMenu(
            bar, values=[m["label"] for m in AVAILABLE_MODELS],
            variable=self._model_var,
            font=cfg.FONTS["small"],
            fg_color=cfg.COLORS["bg_card"],
            button_color=cfg.COLORS["bg_card"],
            button_hover_color=cfg.COLORS["border"],
            text_color=cfg.COLORS["accent"],
            dropdown_fg_color=cfg.COLORS["bg_panel"],
            dropdown_text_color=cfg.COLORS["text_primary"],
            dropdown_hover_color=cfg.COLORS["bg_card"],
            width=190, height=32,
            command=self._on_model_change
        ).grid(row=0, column=0, padx=14, pady=8)

        self._status_label = ctk.CTkLabel(
            bar, text="●  prêt",
            font=cfg.FONTS["small"], text_color=cfg.COLORS["text_dim"]
        )
        self._status_label.grid(row=0, column=2, padx=14)

    def _build_msgarea(self):
        self._msg_frame = ctk.CTkScrollableFrame(
            self, fg_color=cfg.COLORS["bg_dark"],
            scrollbar_button_color=cfg.COLORS["border"]
        )
        self._msg_frame.grid(row=1, column=0, sticky="nsew")
        self._msg_frame.columnconfigure(0, weight=1)

        self._empty_label = ctk.CTkLabel(
            self._msg_frame,
            text="[LaTaverneAI]\n\nDémarrez une conversation.",
            font=cfg.FONTS["heading"],
            text_color=cfg.COLORS["text_dim"],
            justify="center"
        )
        self._empty_label.grid(row=0, column=0, pady=120)

    def _build_inputbar(self):
        bar = ctk.CTkFrame(self, fg_color=cfg.COLORS["bg_panel"], corner_radius=0)
        bar.grid(row=2, column=0, sticky="ew")
        bar.columnconfigure(0, weight=1)

        inner = ctk.CTkFrame(bar, fg_color="transparent")
        inner.pack(fill="x", padx=16, pady=12)
        inner.columnconfigure(0, weight=1)

        self._input = ctk.CTkTextbox(
            inner, height=30, font=cfg.FONTS["body"],
            fg_color=cfg.COLORS["bg_card"],
            border_color=cfg.COLORS["border"], border_width=1,
            text_color=cfg.COLORS["text_primary"],
            corner_radius=10, wrap="word"
        )
        self._input.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        self._input.bind("<Return>", self._on_enter)

        self._send_btn = ctk.CTkButton(
            inner, text="➤", width=44, height=30,
            font=(DEFAULT_FONT, 16),
            fg_color=cfg.COLORS["accent"], hover_color=cfg.COLORS["accent_dim"],
            text_color="#0A0E1A", corner_radius=10,
            command=self._send
        )
        self._send_btn.grid(row=0, column=1)

    # ─── Events ──────────────────────────────────────────────────────────────

    def _on_model_change(self, label):
        for m in AVAILABLE_MODELS:
            if m["label"] == label:
                self._model_id = m["id"]; break

    def _on_enter(self, event):
        if not (event.state & 0x1):
            self._send(); return "break"

    def _on_configure(self, event=None):
        for w in self._md_widgets:
            if w.winfo_exists():
                try: auto_resize_text_widget(w)
                except: pass

    # ─── Conversation management ──────────────────────────────────────────────

    def load_conversation(self, conv_id: int):
        self._conv_id = conv_id
        self._clear_messages()
        messages = get_messages(conv_id)
        for msg in messages:
            self._add_bubble(msg["role"], msg["content"],
                             reasoning=msg.get("reasoning"),
                             model_id=msg.get("model_id"),
                             animate=False)
        if messages:
            self._empty_label.grid_remove()
        self._scroll_bottom()

    def new_conversation(self):
        self._conv_id = None
        self._clear_messages()
        self._empty_label.grid()

    def _clear_messages(self):
        for w in self._msg_frame.winfo_children():
            if w != self._empty_label:
                w.destroy()
        self._row = 1
        self._md_widgets.clear()

    # ─── Send / receive ───────────────────────────────────────────────────────

    def _send(self):
        if self._loading: return
        text = self._input.get("1.0", "end").strip()
        if not text: return
        self._input.delete("1.0", "end")
        self._empty_label.grid_remove()

        if self._conv_id is None and self.user["id"] != 0:
            self._conv_id = create_conversation(self.user["id"], self._model_id)
            self.on_conv_created(self._conv_id)

        if self._conv_id:
            add_message(self._conv_id, "user", text)
        self._add_bubble("user", text)

        self._set_loading(True)
        ctx = (get_conversation_context(self._conv_id)
               if self._conv_id else [{"role": "user", "content": text}])
               
        sys_prompt = None
        if self.user["id"] != 0:
            settings = load_settings(self.user["id"])
            sys_prompt = settings.get("ai", {}).get("system_prompt", "")
               
        threading.Thread(target=self._fetch, args=(ctx, text, sys_prompt), daemon=True).start()

    def _fetch(self, context, user_text, sys_prompt):
        try:
            result = send_message(context, self._model_id, system_prompt=sys_prompt if sys_prompt else None)
            self.after(0, self._on_response, result, user_text)
        except Exception as e:
            self.after(0, self._on_error, str(e))

    def _on_response(self, result, user_text):
        self._set_loading(False)
        content = result["content"]
        reasoning = result.get("reasoning")
        model_id = result["model_id"]

        if self._conv_id:
            add_message(self._conv_id, "assistant", content,
                        reasoning=reasoning, model_id=model_id)
            msgs = get_messages(self._conv_id)
            if len(msgs) <= 2:
                title = generate_title(user_text, self._model_id)
                rename_conversation(self._conv_id, title)
                self.on_conv_created(self._conv_id)

        self._add_bubble("assistant", content, reasoning=reasoning,
                         model_id=model_id, animate=True)

    def _on_error(self, error):
        self._set_loading(False)
        self._add_bubble("system", f"Erreur : {error}")

    def _set_loading(self, state):
        self._loading = state
        if state:
            self._send_btn.configure(text="•••", state="disabled",
                                     fg_color=cfg.COLORS["border"])
            self._status_label.configure(text="●  génération...",
                                          text_color=cfg.COLORS["warning"])
        else:
            self._send_btn.configure(text="➤", state="normal",
                                     fg_color=cfg.COLORS["accent"])
            self._status_label.configure(text="●  prêt",
                                          text_color=cfg.COLORS["text_dim"])

    # ─── Bubbles ─────────────────────────────────────────────────────────────

    def _add_bubble(self, role, content, reasoning=None, model_id=None, animate=False):
        outer = ctk.CTkFrame(self._msg_frame, fg_color="transparent")
        outer.grid(row=self._row, column=0, sticky="ew", padx=16, pady=6)
        outer.columnconfigure(0, weight=1)
        self._row += 1

        if role == "user":
            self._bubble_user(outer, content)
        elif role == "assistant":
            self._bubble_assistant(outer, content, reasoning=reasoning,
                                   model_id=model_id, animate=animate)
        else:
            self._bubble_system(outer, content)
        self._scroll_bottom()

    def _scroll_bottom(self):
        self.after(80, lambda: self._msg_frame._parent_canvas.yview_moveto(1.0))

    def _bubble_user(self, parent, content):
        align = ctk.CTkFrame(parent, fg_color="transparent")
        align.pack(anchor="e")
        ctk.CTkLabel(align, text="Vous", font=(DEFAULT_FONT, 10, "bold"),
                     text_color=cfg.COLORS["accent"]).pack(anchor="e", pady=(0, 3))
        ctk.CTkLabel(align, text=content, font=cfg.FONTS["body"],
                     fg_color=cfg.COLORS["user_bubble"],
                     text_color=cfg.COLORS["text_primary"],
                     corner_radius=14, wraplength=420, justify="left",
                     padx=14, pady=10).pack()

    def _bubble_assistant(self, parent, content, reasoning=None,
                          model_id=None, animate=False):
        align = ctk.CTkFrame(parent, fg_color="transparent")
        align.pack(anchor="w", fill="x")

        model_name = _model_label(model_id) if model_id else "AI"
        ctk.CTkLabel(align, text=f"⬡  {model_name}",
                     font=(DEFAULT_FONT, 10, "bold"),
                     text_color=cfg.COLORS["text_dim"]).pack(anchor="w", pady=(0, 3))

        bubble = ctk.CTkFrame(align, fg_color=cfg.COLORS["ai_bubble"],
                              corner_radius=14, border_width=1,
                              border_color=cfg.COLORS["border"])
        bubble.pack(anchor="w", fill="x", padx=(0, 60), pady=2)
        bubble.columnconfigure(0, weight=1)

        md = create_markdown_text_widget(bubble, bg_color=cfg.COLORS["ai_bubble"])
        md.pack(fill="x", padx=2, pady=2)
        self._md_widgets.append(md)

        if animate:
            def on_step():
                self._resize_md(md)
                self._scroll_bottom()

            def on_done():
                self._resize_md(md)
                self._scroll_bottom()

            animate_markdown_to_widget(md, content, self,
                                       on_step=on_step, on_complete=on_done)
        else:
            render_markdown_to_widget(md, content)
            self.after(20, lambda: self._resize_md(md))

        # Copy button
        action_bar = ctk.CTkFrame(align, fg_color="transparent")
        action_bar.pack(anchor="w", pady=(2, 0))

        def copy_text():
            self.clipboard_clear()
            self.clipboard_append(content)
            cb.configure(text="✓ copié")
            self.after(1500, lambda: cb.configure(text="⎘  Copier"))

        cb = ctk.CTkButton(action_bar, text="⎘  Copier", width=80, height=24,
                           font=(DEFAULT_FONT, 10), fg_color="transparent",
                           hover_color=cfg.COLORS["bg_card"],
                           text_color=cfg.COLORS["text_dim"],
                           corner_radius=6, command=copy_text)
        cb.pack(side="left")

    def _resize_md(self, widget):
        if widget.winfo_exists():
            try: auto_resize_text_widget(widget)
            except: pass

    def _bubble_system(self, parent, content):
        ctk.CTkLabel(parent, text=content, font=cfg.FONTS["small"],
                     text_color=cfg.COLORS["danger"], justify="center").pack()