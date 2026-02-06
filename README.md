# MCP Notion pour n8n

Serveur MCP (Model Context Protocol) qui expose **toute l'API Notion** comme outils pour un agent IA dans n8n. Ton agent peut créer des pages, gérer des databases, écrire du contenu, commenter, chercher — bref, tout faire à ta place.

## Architecture

Tu as **deux approches** qui fonctionnent ensemble :

```
                         ┌─ Approche A ──────────────────────────────────────┐
                         │                                                   │
┌──────────┐   WhatsApp  │  ┌────────────────┐  SSE   ┌──────────────────┐  │   ┌─────────┐
│ Téléphone│────────────►│  │  n8n           │◄──────►│ MCP Notion       │──│──►│ Notion  │
│          │◄────────────│  │  (AI Agent)    │        │ Server (externe) │  │   │  API    │
└──────────┘             │  └───────┬────────┘        └──────────────────┘  │   └─────────┘
                         │          │                                       │
                         │          │  Approche B ──────────────────────┐   │
                         │          │                                   │   │
                         │          └──► MCP Server n8n ──► Notion     │   │
                         │               (natif, tools n8n)  Tools     │   │
                         │                                              │   │
                         └──────────────────────────────────────────────┘   │
```

**Approche A** — Serveur MCP externe (TypeScript) : Flexible, 17 outils, supporte filtres avancés, commentaires, utilisateurs. Tourne dans Docker à côté de n8n.

**Approche B** — MCP Server n8n natif : Utilise les noeuds Notion de n8n directement comme outils MCP. 11 outils, plus simple, zéro code.

## Outils disponibles

### Approche A — Serveur MCP externe (17 outils)

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

### Approche B — MCP Server n8n natif (11 outils)

| Outil | Description |
|-------|-------------|
| Create Page | Créer une page sous un parent |
| Get Page | Lire les propriétés d'une page |
| Update Page | Modifier titre, statut, tags, dates |
| Delete Page | Archiver une page |
| Search Pages | Chercher dans tout le workspace |
| Get Database | Voir le schéma d'une DB |
| Create Database Entry | Ajouter une entrée |
| Update Database Entry | Modifier une entrée |
| Query Database | Lister les entrées d'une DB |
| Append Content to Page | Ajouter du contenu (blocs) |
| Get Page Content | Lire le contenu complet d'une page |

---

## Démarrage rapide

### Étape 1 — Créer l'intégration Notion

1. Va sur https://www.notion.so/my-integrations
2. Clique **"Nouvelle intégration"**
3. Nom : `Mon Agent IA` (ou ce que tu veux)
4. Capacités : **Lire**, **Mettre à jour**, **Insérer du contenu**
5. Copie le **token** (commence par `ntn_`)

### Étape 2 — Partager avec l'intégration

Dans Notion, pour **chaque page ou database** que l'agent doit gérer :
- Clique **"..."** en haut à droite → **"Connexions"** → ajoute ton intégration

> Astuce : partage une page racine et toutes les sous-pages héritent de l'accès.

### Étape 3 — Configuration

```bash
cp .env.example .env
nano .env   # Colle ta NOTION_API_KEY
```

### Étape 4 — Lancer avec Docker

```bash
docker compose up -d
```

| Service | URL |
|---------|-----|
| n8n | http://localhost:5678 |
| MCP Notion Server | http://localhost:3001 |
| Health check | http://localhost:3001/health |

### Étape 5 — Configurer n8n

#### Option A : Utiliser le serveur MCP externe

1. Dans n8n, va dans **Settings** → **Variables**
2. Ajoute : `MCP_NOTION_URL` = `http://notion-mcp:3001/sse`
3. Le noeud **"Notion mcp"** dans le workflow utilise déjà cette variable

#### Option B : Utiliser le MCP server n8n natif

1. Importe `n8n/workflows/whatsapp-ai-assistant.json` dans n8n
2. Les noeuds Notion sont déjà connectés au trigger **"Notion MCP"**
3. Configure tes credentials Notion dans n8n (Settings → Credentials → Notion API)
4. Dans **Settings** → **Variables**, mets : `MCP_NOTION_URL` = `http://localhost:5678/mcp/notion-mcp-server/sse`

### Étape 6 — Importer le workflow

1. Ouvre n8n → **Workflows** → **Import from file**
2. Sélectionne `n8n/workflows/whatsapp-ai-assistant.json`
3. Configure tes credentials :
   - **OpenAI** (pour le LLM GPT-4.1-mini)
   - **Notion** (pour les outils natifs)
   - **Evolution API** (pour WhatsApp)
   - **Google Calendar**, **Gmail**, **Google Contacts** (optionnel)
4. Mets les variables d'environnement MCP dans n8n
5. Active le workflow

---

## Utilisation sans Docker

```bash
npm install

# Mode SSE (pour n8n)
npm run dev:sse

# Mode stdio (pour Claude Desktop)
npm run dev
```

## Configuration Claude Desktop

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

## Exemples de prompts WhatsApp

Une fois tout activé, envoie un message WhatsApp à ton agent :

- *"Cherche toutes mes tâches en cours dans Notion"*
- *"Crée une page Compte-rendu réunion avec les points suivants : ..."*
- *"Ajoute une entrée dans ma database Projets avec le statut En cours"*
- *"Liste toutes mes databases"*
- *"Modifie le statut de la tâche X en Terminé"*
- *"Crée une database Suivi Budget avec les colonnes : Nom, Montant, Date, Catégorie"*
- *"Mets un commentaire sur la page Planning : RDV confirmé"*
- *"Lis le contenu de la page Roadmap Q1"*

## Structure du projet

```
.
├── src/
│   ├── index.ts              # Point d'entrée MCP server (SSE + stdio)
│   └── notion/
│       ├── client.ts          # Client Notion API
│       └── tools.ts           # 17 outils MCP enregistrés
├── n8n/
│   └── workflows/
│       ├── whatsapp-ai-assistant.json   # Workflow complet (WhatsApp + tous MCP)
│       └── notion-ai-agent.json         # Workflow simplifié (chat + Notion MCP)
├── docker-compose.yml         # n8n + MCP server
├── Dockerfile                 # Build du MCP server
├── .env.example               # Template de configuration
└── package.json
```

## Ce qui a été corrigé dans le workflow

Par rapport au workflow original, voici les corrections apportées :

1. **Connexions MCP manquantes** — Les noeuds Notion (Create Page, Get Page, etc.) n'étaient pas connectés au trigger "Notion MCP". Ajout de toutes les connexions `ai_tool`.

2. **Connexions Calendar/Gmail/Contacts** — Idem, les tool nodes n'étaient pas reliés à leurs MCP triggers respectifs. Toutes les connexions ont été ajoutées.

3. **Tool descriptions** — Ajout de `descriptionType: "manual"` et `toolDescription` sur tous les noeuds Notion pour que l'IA comprenne quand et comment utiliser chaque outil.

4. **Type des noeuds Notion** — Conversion de `n8n-nodes-base.notion` vers `n8n-nodes-base.notionTool` (typeVersion 2.1) pour qu'ils soient utilisables comme outils IA.

5. **System prompt enrichi** — Ajout des instructions Notion dans le prompt du Control center avec la règle "utilise notion_search d'abord".
