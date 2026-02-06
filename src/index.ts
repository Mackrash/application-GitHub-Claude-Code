import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { SSEServerTransport } from "@modelcontextprotocol/sdk/server/sse.js";
import express from "express";
import { registerNotionTools } from "./notion/tools.js";

const server = new McpServer({
  name: "notion-mcp",
  version: "1.0.0",
  capabilities: {
    tools: {},
  },
});

// Enregistrer tous les outils Notion
registerNotionTools(server);

// ─── Démarrage ────────────────────────────────────────────

const transport = process.env.MCP_TRANSPORT ?? "stdio";

if (transport === "sse") {
  // Mode SSE — accessible via réseau (pour n8n, etc.)
  const app = express();
  const port = parseInt(process.env.MCP_PORT ?? "3001", 10);

  // Map des transports SSE actifs
  const transports = new Map<string, SSEServerTransport>();

  app.get("/sse", async (req, res) => {
    const sseTransport = new SSEServerTransport("/messages", res);
    transports.set(sseTransport.sessionId, sseTransport);

    res.on("close", () => {
      transports.delete(sseTransport.sessionId);
    });

    await server.connect(sseTransport);
  });

  app.post("/messages", async (req, res) => {
    const sessionId = req.query.sessionId as string;
    const sseTransport = transports.get(sessionId);
    if (!sseTransport) {
      res.status(400).json({ error: "Session inconnue" });
      return;
    }
    await sseTransport.handlePostMessage(req, res);
  });

  app.get("/health", (_req, res) => {
    res.json({ status: "ok", tools: "notion-mcp", transport: "sse" });
  });

  app.listen(port, () => {
    console.log(`🔌 Notion MCP Server (SSE) démarré sur http://0.0.0.0:${port}`);
    console.log(`   SSE endpoint:     http://localhost:${port}/sse`);
    console.log(`   Messages endpoint: http://localhost:${port}/messages`);
    console.log(`   Health check:     http://localhost:${port}/health`);
  });
} else {
  // Mode stdio — pour Claude Desktop ou test local
  const stdioTransport = new StdioServerTransport();
  await server.connect(stdioTransport);
  console.error("🔌 Notion MCP Server (stdio) démarré");
}
