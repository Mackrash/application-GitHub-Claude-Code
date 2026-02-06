import { Client } from "@notionhq/client";

let notionClient: Client | null = null;

export function getNotionClient(): Client {
  if (!notionClient) {
    const apiKey = process.env.NOTION_API_KEY;
    if (!apiKey) {
      throw new Error(
        "NOTION_API_KEY manquante. Définis-la dans ton fichier .env"
      );
    }
    notionClient = new Client({ auth: apiKey });
  }
  return notionClient;
}
