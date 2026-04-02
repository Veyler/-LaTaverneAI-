# NexusChat

Interface de chat moderne pour interagir avec des modèles IA via l'API NVIDIA/OpenAI.

## Structure du projet

```
chatapp/
├── main.py                  # Point d'entrée
├── requirements.txt
├── chatapp.db               # Base SQLite (créée automatiquement)
│
├── core/
│   ├── config.py            # ⚙️  Configuration centrale (modèles, couleurs, etc.)
│   ├── database.py          # Couche BDD (users, conversations, messages)
│   └── api_client.py        # Wrapper API OpenAI/NVIDIA
│
└── ui/
    ├── auth_screen.py       # Écran login / création de compte
    ├── sidebar.py           # Sidebar avec historique des conversations
    └── chat_view.py         # Zone de chat principale
```

## Installation

```bash
pip install -r requirements.txt
python main.py
```

## Ajouter un modèle

Dans `core/config.py`, ajouter un entrée dans `AVAILABLE_MODELS` :

```python
{
    "label": "Mon Modèle",
    "id": "provider/model-name",
    "description": "Description du modèle",
    "max_tokens": 4096,
    "supports_reasoning": False,
},
```

## Fonctionnalités

- ✅ Création de compte / connexion (hashage SHA-256 + salt)
- ✅ Mode invité (sans compte)
- ✅ Historique des conversations par utilisateur (SQLite)
- ✅ Sélecteur de modèle en temps réel
- ✅ Affichage du raisonnement (reasoning_content) collapsible
- ✅ Titre auto-généré pour chaque conversation
- ✅ Suppression de conversations
- ✅ UI sombre style terminal / cyberpunk
- ✅ Multi-utilisateurs

## Évolutions suggérées

- Streaming de la réponse token par token
- Export des conversations en Markdown/PDF
- Paramètres par conversation (température, top_p...)
- Thèmes clairs/sombres switchables
- Raccourcis clavier
- Recherche dans l'historique
