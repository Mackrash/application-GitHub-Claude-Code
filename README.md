# MCP Notion pour n8n

Serveur MCP (Model Context Protocol) qui expose **toute l'API Notion** comme outils pour un agent IA dans n8n. Ton agent peut créer des pages, gérer des databases, écrire du contenu, commenter, chercher — bref, tout faire à ta place.

## Architecture

```
┌─────────────┐     SSE      ┌──────────────────┐     API     ┌─────────┐
│     n8n      │◄────────────►│  MCP Notion      │◄───────────►│ Notion  │
│  (AI Agent)  │              │  Server          │             │   API   │
└─────────────┘              └──────────────────┘             └─────────┘
```

L'agent IA dans n8n se connecte au serveur MCP via SSE. Le serveur MCP traduit les appels d'outils en requêtes vers l'API Notion.

## Outils disponibles (17 outils)

| Catégorie | Outil | Description |
|-----------|-------|-------------|
| **Recherche** | `notion_search` | Rechercher pages et databases |
| **Pages** | `notion_get_page` | Lire une page |
| | `notion_create_page` | Créer une page (dans une DB ou sous une page) |
| | `notion_update_page` | Modifier les propriétés d'une page |
| **Databases** | `notion_get_database` | Voir le schéma d'une database |
| | `notion_query_database` | Requêter avec filtres et tri |
| | `notion_create_database` | Créer une nouvelle database |
| | `notion_update_database` | Modifier le schéma |
| **Blocs** | `notion_get_block_children` | Lire le contenu d'une page |
| | `notion_append_blocks` | Ajouter du contenu |
| | `notion_update_block` | Modifier un bloc |
| | `notion_delete_block` | Supprimer un bloc |
| **Commentaires** | `notion_list_comments` | Lister les commentaires |
| | `notion_add_comment` | Ajouter un commentaire |
| **Utilisateurs** | `notion_list_users` | Lister les utilisateurs |
| | `notion_get_user` | Infos d'un utilisateur |

## Démarrage rapide

### 1. Prérequis

- Docker et Docker Compose
- Une [intégration Notion](https://www.notion.so/my-integrations) (pour obtenir la clé API)

### 2. Configuration

```bash
# Copie le fichier d'exemple
cp .env.example .env

# Édite avec ta clé Notion
nano .env
```

Remplis au minimum :
```
NOTION_API_KEY=ntn_ton_token_ici
```

### 3. Partager avec l'intégration

Dans Notion, va sur chaque page/database que tu veux rendre accessible et clique sur **"..."** → **"Connexions"** → ajoute ton intégration.

### 4. Lancer

```bash
docker compose up -d
```

- **n8n** : http://localhost:5678
- **MCP Server** : http://localhost:3001
- **Health check** : http://localhost:3001/health

### 5. Configurer le workflow n8n

1. Ouvre n8n (http://localhost:5678)
2. Importe le workflow depuis `n8n/workflows/notion-ai-agent.json`
3. Configure tes credentials OpenAI (ou autre LLM)
4. Le noeud **MCP Client** pointe déjà vers `http://notion-mcp:3001/sse`
5. Active le workflow et ouvre le chat

## Utilisation sans Docker

```bash
# Installer les dépendances
npm install

# Mode SSE (pour n8n)
cp .env.example .env
# édite .env avec ta NOTION_API_KEY
npm run dev:sse

# Mode stdio (pour Claude Desktop)
npm run dev
```

## Configuration Claude Desktop

Pour utiliser ce MCP avec Claude Desktop, ajoute dans `claude_desktop_config.json` :

```json
{
  "mcpServers": {
    "notion": {
      "command": "node",
      "args": ["/chemin/vers/dist/index.js"],
      "env": {
        "NOTION_API_KEY": "ntn_ton_token_ici"
      }
    }
  }
}
```

## Exemples de prompts pour l'agent

Une fois le workflow n8n activé, tu peux demander à l'agent :

- *"Cherche toutes mes tâches en cours dans Notion"*
- *"Crée une page 'Compte-rendu réunion' avec les notes suivantes..."*
- *"Ajoute une entrée dans ma database Projets avec le statut 'En cours'"*
- *"Liste toutes mes databases Notion"*
- *"Modifie le statut de la tâche X en 'Terminé'"*
- *"Crée une database 'Suivi Budget' avec les colonnes : Nom, Montant, Date, Catégorie"*
