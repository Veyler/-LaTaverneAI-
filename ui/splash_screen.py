import customtkinter as ctk
import os
import sys
from core.config import APP_NAME, APP_VERSION, COLORS, FONTS

class SplashScreen(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        
        # Fenêtre sans bordures
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.configure(fg_color=COLORS["bg_dark"])
        
        # Centrer la fenêtre
        width = 400
        height = 250
        self.geometry(f"{width}x{height}")
        self.update_idletasks()
        
        # Calcul du placement au centre
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")
        
        # Affichage du Splash Screen
        self._build_ui()
        
    def _build_ui(self):
        # Conteneur principal
        container = ctk.CTkFrame(self, fg_color=COLORS["bg_dark"], corner_radius=0, border_width=2, border_color=COLORS["accent"])
        container.pack(fill="both", expand=True)
        
        # Titre
        self.lbl_title = ctk.CTkLabel(
            container, 
            text=APP_NAME, 
            font=FONTS["title"], 
            text_color=COLORS["accent"]
        )
        self.lbl_title.pack(pady=(60, 5))
        
        # Version
        self.lbl_version = ctk.CTkLabel(
            container, 
            text=f"Version {APP_VERSION}", 
            font=FONTS["small"], 
            text_color=COLORS["text_dim"]
        )
        self.lbl_version.pack(pady=0)
        
        # Status de progression / Maj
        self.lbl_status = ctk.CTkLabel(
            container, 
            text="Initialisation...", 
            font=FONTS["body"], 
            text_color=COLORS["text_primary"]
        )
        self.lbl_status.pack(pady=(40, 20))
        
    def update_status(self, text: str):
        """Met à jour le texte affiché sur la fenêtre de chargement."""
        self.lbl_status.configure(text=text)
        self.update()  # Forcer le redessin de l'interface
