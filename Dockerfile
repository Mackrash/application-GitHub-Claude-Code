FROM node:20-slim

WORKDIR /app

COPY package.json ./
RUN npm install

COPY tsconfig.json ./
COPY src/ ./src/

RUN npm run build

ENV MCP_TRANSPORT=sse
ENV MCP_PORT=3001

EXPOSE 3001

CMD ["node", "dist/index.js"]
