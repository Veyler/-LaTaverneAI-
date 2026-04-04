# LaTaverneAI

Interface de chat moderne pour interagir avec des modèles IA via des API (ex: NVIDIA, OpenAI).

## Structure du projet

```
LaTaverneAI/
├── main.py                  # Point d'entrée
├── requirements.txt
├── chatapp.db               # Base SQLite (créée automatiquement)
├── LaTaverneAI.spec         # Fichier de build PyInstaller
├── setup.iss                # Script Inno Setup pour créer l'installeur
│
├── core/
│   ├── config.py            # ⚙️  Configuration centrale (modèles, etc.)
│   ├── database.py          # Couche BDD (users, conversations, messages)
│   └── api_client.py        # Wrapper API
│
├── ui/
│   ├── auth_screen.py       # Écran login / création de compte
│   ├── sidebar.py           # Sidebar avec historique des conversations
│   └── chat_view.py         # Zone de chat principale
│
└── user_settings/           # Fichiers de configuration utilisateur (ex: couleurs, prompts)
```

## Installation

```bash
pip install -r requirements.txt
python main.py
```

## Compilation (.exe)

Pour compiler l'application en exécutable avec PyInstaller :

```bash
pyinstaller LaTaverneAI.spec
```
Pour créer l'installeur, utilisez Inno Setup avec le fichier `setup.iss`.

## Fonctionnalités

- ✅ Création de compte / connexion (hashage SHA-256 + salt)
- ✅ Mode invité (sans compte)
- ✅ Historique des conversations par utilisateur (SQLite)
- ✅ Sélecteur de modèle en temps réel
- ✅ Affichage du raisonnement cognitif (reasoning_content) collapsible
- ✅ Titre auto-généré pour chaque conversation
- ✅ Suppression de conversations
- ✅ Panneau de paramètres (personnalisation de la couleur d'accentuation et du System Prompt)
- ✅ UI sombre cyberpunk moderne
- ✅ Multi-utilisateurs

## Évolutions suggérées

- Streaming de la réponse token par token
- Export des conversations en Markdown/PDF
- Paramètres avancés par conversation (température, top_p...)
- Thèmes clairs/sombres switchables
- Raccourcis clavier
- Recherche précise dans l'historique
