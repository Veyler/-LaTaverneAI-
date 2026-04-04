import os
import sys
import tempfile
import requests
import threading
from urllib.error import URLError
from core.config import APP_VERSION

GITHUB_API_URL = "https://api.github.com/repos/Veyler/-LaTaverneAI-/releases/latest"

def _parse_version(version_str: str) -> tuple:
    """Transforme une chaîne de version 'v1.2.3' ou '1.2.3' en tuple (1, 2, 3)."""
    clean_str = version_str.lower().strip("v ")
    try:
        return tuple(map(int, clean_str.split('.')))
    except ValueError:
        return (0, 0, 0)

def check_for_updates() -> dict | None:
    """Vérifie si une mise à jour est disponible sur Github."""
    try:
        response = requests.get(GITHUB_API_URL, timeout=5)
        response.raise_for_status()
        data = response.json()
        
        latest_version_str = data.get("tag_name", "")
        latest_version = _parse_version(latest_version_str)
        current_version = _parse_version(APP_VERSION)
        
        if latest_version > current_version:
            # Cherche l'asset exécutable de l'installateur
            assets = data.get("assets", [])
            download_url = None
            for asset in assets:
                if asset.get("name", "").endswith(".exe"):
                    download_url = asset.get("browser_download_url")
                    break
                    
            if download_url:
                return {
                    "version": latest_version_str,
                    "url": download_url
                }
    except Exception as e:
        print(f"Erreur lors de la vérification des mises à jour: {e}")
    
    return None


def download_and_install_update(url: str, update_callback=None):
    """Télécharge l'exécutable et le lance, puis quitte l'application."""
    try:
        if update_callback:
            update_callback("Téléchargement de la mise à jour...")
            
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            installer_path = os.path.join(tempfile.gettempdir(), "LaTaverneAI_Update.exe")
            
            with open(installer_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
                    
        if update_callback:
            update_callback("Lancement de l'installateur...")
            
        # Lancement de l'installateur sous Windows
        os.startfile(installer_path)
        
        # Fermeture de l'application pour que l'installateur puisse écraser les fichiers
        sys.exit(0)
    except Exception as e:
        print(f"Erreur lors de la mise à jour: {e}")
        if update_callback:
            update_callback(f"Erreur: {e}")
