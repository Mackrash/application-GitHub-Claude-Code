import { z } from "zod";
import type { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { getNotionClient } from "./client.js";

// ─── Helpers ──────────────────────────────────────────────

function truncate(obj: unknown, maxLen = 8000): string {
  const str = JSON.stringify(obj, null, 2);
  if (str.length <= maxLen) return str;
  return str.slice(0, maxLen) + "\n... (tronqué)";
}

// ─── Register all Notion tools ────────────────────────────

export function registerNotionTools(server: McpServer) {
  // ════════════════════════════════════════════════════════
  // 1. SEARCH
  // ════════════════════════════════════════════════════════

  server.tool(
    "notion_search",
    "Rechercher des pages et databases dans Notion",
    {
      query: z.string().describe("Texte à rechercher"),
      filter: z
        .enum(["page", "database"])
        .optional()
        .describe("Filtrer par type: page ou database"),
      page_size: z
        .number()
        .min(1)
        .max(100)
        .optional()
        .describe("Nombre de résultats (max 100)"),
    },
    async ({ query, filter, page_size }) => {
      const notion = getNotionClient();
      const params: Parameters<typeof notion.search>[0] = {
        query,
        page_size: page_size ?? 20,
      };
      if (filter) {
        params.filter = { value: filter, property: "object" };
      }
      const response = await notion.search(params);
      return {
        content: [{ type: "text", text: truncate(response.results) }],
      };
    }
  );

  // ════════════════════════════════════════════════════════
  // 2. PAGES
  // ════════════════════════════════════════════════════════

  server.tool(
    "notion_get_page",
    "Récupérer les propriétés d'une page Notion",
    {
      page_id: z.string().describe("ID de la page Notion"),
    },
    async ({ page_id }) => {
      const notion = getNotionClient();
      const page = await notion.pages.retrieve({ page_id });
      return { content: [{ type: "text", text: truncate(page) }] };
    }
  );

  server.tool(
    "notion_create_page",
    "Créer une nouvelle page dans une database ou comme enfant d'une page",
    {
      parent_type: z
        .enum(["database_id", "page_id"])
        .describe("Type de parent: database_id ou page_id"),
      parent_id: z.string().describe("ID du parent (database ou page)"),
      properties: z
        .string()
        .describe("Propriétés de la page en JSON (ex: titre, champs de la DB)"),
      children: z
        .string()
        .optional()
        .describe("Contenu de la page en JSON (tableau de blocs Notion)"),
      icon: z
        .string()
        .optional()
        .describe("Emoji pour l'icône de la page (ex: '🚀')"),
    },
    async ({ parent_type, parent_id, properties, children, icon }) => {
      const notion = getNotionClient();
      const params: Record<string, unknown> = {
        parent: { [parent_type]: parent_id },
        properties: JSON.parse(properties),
      };
      if (children) {
        params.children = JSON.parse(children);
      }
      if (icon) {
        params.icon = { type: "emoji", emoji: icon };
      }
      const page = await notion.pages.create(params as any);
      return { content: [{ type: "text", text: truncate(page) }] };
    }
  );

  server.tool(
    "notion_update_page",
    "Mettre à jour les propriétés d'une page (titre, statut, champs, etc.)",
    {
      page_id: z.string().describe("ID de la page à modifier"),
      properties: z
        .string()
        .describe("Propriétés à modifier en JSON"),
      archived: z
        .boolean()
        .optional()
        .describe("true pour archiver la page, false pour la restaurer"),
      icon: z
        .string()
        .optional()
        .describe("Nouvel emoji pour l'icône"),
    },
    async ({ page_id, properties, archived, icon }) => {
      const notion = getNotionClient();
      const params: Record<string, unknown> = {
        page_id,
        properties: JSON.parse(properties),
      };
      if (archived !== undefined) params.archived = archived;
      if (icon) params.icon = { type: "emoji", emoji: icon };
      const page = await notion.pages.update(params as any);
      return { content: [{ type: "text", text: truncate(page) }] };
    }
  );

  // ════════════════════════════════════════════════════════
  // 3. DATABASES
  // ════════════════════════════════════════════════════════

  server.tool(
    "notion_get_database",
    "Récupérer le schéma et infos d'une database Notion",
    {
      database_id: z.string().describe("ID de la database"),
    },
    async ({ database_id }) => {
      const notion = getNotionClient();
      const db = await notion.databases.retrieve({ database_id });
      return { content: [{ type: "text", text: truncate(db) }] };
    }
  );

  server.tool(
    "notion_query_database",
    "Requêter une database avec filtres et tri",
    {
      database_id: z.string().describe("ID de la database"),
      filter: z
        .string()
        .optional()
        .describe("Filtre en JSON (format Notion API)"),
      sorts: z
        .string()
        .optional()
        .describe("Tri en JSON (format Notion API)"),
      page_size: z
        .number()
        .min(1)
        .max(100)
        .optional()
        .describe("Nombre de résultats (max 100)"),
      start_cursor: z
        .string()
        .optional()
        .describe("Curseur pour la pagination"),
    },
    async ({ database_id, filter, sorts, page_size, start_cursor }) => {
      const notion = getNotionClient();
      const params: Record<string, unknown> = {
        database_id,
        page_size: page_size ?? 50,
      };
      if (filter) params.filter = JSON.parse(filter);
      if (sorts) params.sorts = JSON.parse(sorts);
      if (start_cursor) params.start_cursor = start_cursor;
      const response = await notion.databases.query(params as any);
      return {
        content: [
          {
            type: "text",
            text: truncate({
              results: response.results,
              has_more: response.has_more,
              next_cursor: response.next_cursor,
            }),
          },
        ],
      };
    }
  );

  server.tool(
    "notion_create_database",
    "Créer une nouvelle database dans une page",
    {
      parent_page_id: z.string().describe("ID de la page parente"),
      title: z.string().describe("Titre de la database"),
      properties: z
        .string()
        .describe(
          "Schéma des colonnes en JSON (ex: {\"Nom\": {\"title\": {}}, \"Statut\": {\"select\": {\"options\": [{\"name\": \"À faire\"}, {\"name\": \"Fait\"}]}}})"
        ),
      icon: z.string().optional().describe("Emoji pour l'icône"),
    },
    async ({ parent_page_id, title, properties, icon }) => {
      const notion = getNotionClient();
      const params: Record<string, unknown> = {
        parent: { page_id: parent_page_id },
        title: [{ type: "text", text: { content: title } }],
        properties: JSON.parse(properties),
      };
      if (icon) params.icon = { type: "emoji", emoji: icon };
      const db = await notion.databases.create(params as any);
      return { content: [{ type: "text", text: truncate(db) }] };
    }
  );

  server.tool(
    "notion_update_database",
    "Modifier le titre ou le schéma d'une database",
    {
      database_id: z.string().describe("ID de la database"),
      title: z.string().optional().describe("Nouveau titre"),
      properties: z
        .string()
        .optional()
        .describe("Modifications du schéma en JSON"),
    },
    async ({ database_id, title, properties }) => {
      const notion = getNotionClient();
      const params: Record<string, unknown> = { database_id };
      if (title) {
        params.title = [{ type: "text", text: { content: title } }];
      }
      if (properties) params.properties = JSON.parse(properties);
      const db = await notion.databases.update(params as any);
      return { content: [{ type: "text", text: truncate(db) }] };
    }
  );

  // ════════════════════════════════════════════════════════
  // 4. BLOCKS (contenu des pages)
  // ════════════════════════════════════════════════════════

  server.tool(
    "notion_get_block_children",
    "Lire le contenu (blocs enfants) d'une page ou d'un bloc",
    {
      block_id: z.string().describe("ID du bloc ou de la page"),
      page_size: z.number().min(1).max(100).optional(),
      start_cursor: z.string().optional(),
    },
    async ({ block_id, page_size, start_cursor }) => {
      const notion = getNotionClient();
      const params: Record<string, unknown> = {
        block_id,
        page_size: page_size ?? 100,
      };
      if (start_cursor) params.start_cursor = start_cursor;
      const response = await notion.blocks.children.list(params as any);
      return {
        content: [
          {
            type: "text",
            text: truncate({
              results: response.results,
              has_more: response.has_more,
              next_cursor: response.next_cursor,
            }),
          },
        ],
      };
    }
  );

  server.tool(
    "notion_append_blocks",
    "Ajouter du contenu (blocs) à une page ou un bloc existant",
    {
      block_id: z
        .string()
        .describe("ID de la page ou du bloc parent"),
      children: z
        .string()
        .describe(
          "Blocs à ajouter en JSON (ex: [{\"object\":\"block\",\"type\":\"paragraph\",\"paragraph\":{\"rich_text\":[{\"text\":{\"content\":\"Hello\"}}]}}])"
        ),
    },
    async ({ block_id, children }) => {
      const notion = getNotionClient();
      const response = await notion.blocks.children.append({
        block_id,
        children: JSON.parse(children),
      });
      return { content: [{ type: "text", text: truncate(response) }] };
    }
  );

  server.tool(
    "notion_update_block",
    "Modifier un bloc existant (texte, todo, heading, etc.)",
    {
      block_id: z.string().describe("ID du bloc à modifier"),
      block_data: z
        .string()
        .describe(
          "Données du bloc en JSON (ex: {\"paragraph\": {\"rich_text\": [{\"text\": {\"content\": \"Nouveau texte\"}}]}})"
        ),
      archived: z
        .boolean()
        .optional()
        .describe("true pour supprimer le bloc"),
    },
    async ({ block_id, block_data, archived }) => {
      const notion = getNotionClient();
      const params: Record<string, unknown> = {
        block_id,
        ...JSON.parse(block_data),
      };
      if (archived !== undefined) params.archived = archived;
      const block = await notion.blocks.update(params as any);
      return { content: [{ type: "text", text: truncate(block) }] };
    }
  );

  server.tool(
    "notion_delete_block",
    "Supprimer un bloc (le mettre en archived)",
    {
      block_id: z.string().describe("ID du bloc à supprimer"),
    },
    async ({ block_id }) => {
      const notion = getNotionClient();
      const block = await notion.blocks.delete({ block_id });
      return { content: [{ type: "text", text: truncate(block) }] };
    }
  );

  // ════════════════════════════════════════════════════════
  // 5. COMMENTS
  // ════════════════════════════════════════════════════════

  server.tool(
    "notion_list_comments",
    "Lister les commentaires d'une page ou d'un bloc",
    {
      block_id: z
        .string()
        .describe("ID de la page ou du bloc"),
      page_size: z.number().min(1).max(100).optional(),
      start_cursor: z.string().optional(),
    },
    async ({ block_id, page_size, start_cursor }) => {
      const notion = getNotionClient();
      const params: Record<string, unknown> = {
        block_id,
        page_size: page_size ?? 50,
      };
      if (start_cursor) params.start_cursor = start_cursor;
      const response = await notion.comments.list(params as any);
      return { content: [{ type: "text", text: truncate(response) }] };
    }
  );

  server.tool(
    "notion_add_comment",
    "Ajouter un commentaire sur une page ou en réponse à une discussion",
    {
      parent_type: z
        .enum(["page_id", "discussion_id"])
        .describe("Type: page_id pour commenter une page, discussion_id pour répondre"),
      parent_id: z.string().describe("ID de la page ou de la discussion"),
      text: z.string().describe("Texte du commentaire"),
    },
    async ({ parent_type, parent_id, text }) => {
      const notion = getNotionClient();
      const params: Record<string, unknown> = {
        [parent_type]: parent_id,
        rich_text: [{ text: { content: text } }],
      };
      const comment = await notion.comments.create(params as any);
      return { content: [{ type: "text", text: truncate(comment) }] };
    }
  );

  // ════════════════════════════════════════════════════════
  // 6. USERS
  // ════════════════════════════════════════════════════════

  server.tool(
    "notion_list_users",
    "Lister tous les utilisateurs du workspace Notion",
    {},
    async () => {
      const notion = getNotionClient();
      const response = await notion.users.list({});
      return { content: [{ type: "text", text: truncate(response.results) }] };
    }
  );

  server.tool(
    "notion_get_user",
    "Récupérer les infos d'un utilisateur Notion",
    {
      user_id: z.string().describe("ID de l'utilisateur"),
    },
    async ({ user_id }) => {
      const notion = getNotionClient();
      const user = await notion.users.retrieve({ user_id });
      return { content: [{ type: "text", text: truncate(user) }] };
    }
  );
}
