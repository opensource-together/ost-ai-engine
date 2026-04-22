# OST MCP Server Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a TypeScript MCP server distributed via `npx @opensource-together/mcp` that exposes OST Linker project data as tools for Claude Desktop, IDEs, and other MCP clients.

**Architecture:** Lightweight TypeScript MCP server using `@modelcontextprotocol/sdk` with stdio transport. Fetches data from the ost-linker FastAPI REST API. Auto-generated TypeScript client from OpenAPI schema ensures type safety.

**Tech Stack:** TypeScript, `@modelcontextprotocol/sdk`, `openapi-fetch`, Node.js

**Spec:** (in ost-linker repo) `specs/2026-03-10-mcp-server-design.md`

**Repo:** `/home/spidey/git/ost-mcp`

---

## File Structure

```
ost-mcp/
├── src/
│   ├── index.ts              # MCP server entry point
│   ├── config.ts             # Read OST_API_URL from env
│   ├── client.ts             # HTTP client wrapper for the API
│   ├── tools/
│   │   ├── search.ts         # search_projects tool
│   │   ├── project.ts        # get_project tool
│   │   ├── trending.ts       # get_trending tool
│   │   ├── similar.ts        # find_similar tool
│   │   └── references.ts     # list_categories, list_domains, list_techstacks
│   └── types.ts              # Shared types (auto-generated or manual)
├── tests/
│   ├── config.test.ts
│   ├── client.test.ts
│   └── tools/
│       ├── search.test.ts
│       ├── project.test.ts
│       ├── trending.test.ts
│       ├── similar.test.ts
│       └── references.test.ts
├── package.json
├── tsconfig.json
├── vitest.config.ts
├── CLAUDE.md
├── .claude/
│   └── rules/
│       └── conventions.md
└── .github/
    └── workflows/
        └── ci.yml
```

---

## Chunk 1: Project scaffolding

### Task 1: Initialize the project

**Files:**
- Create: `package.json`
- Create: `tsconfig.json`
- Create: `vitest.config.ts`
- Create: `.gitignore`

- [ ] **Step 1: Initialize npm package**

```bash
cd /home/spidey/git/ost-mcp
npm init -y
```

Then edit `package.json`:
```json
{
  "name": "@opensource-together/mcp",
  "version": "0.1.0",
  "description": "MCP server for discovering open-source projects via OST Linker",
  "type": "module",
  "bin": {
    "ost-mcp": "./dist/index.js"
  },
  "scripts": {
    "build": "tsc",
    "dev": "tsc --watch",
    "start": "node dist/index.js",
    "test": "vitest run",
    "test:watch": "vitest",
    "lint": "tsc --noEmit",
    "prepublishOnly": "npm run build"
  },
  "keywords": ["mcp", "open-source", "recommendations"],
  "license": "MIT",
  "repository": {
    "type": "git",
    "url": "https://github.com/opensource-together/ost-mcp"
  }
}
```

- [ ] **Step 2: Install dependencies**

```bash
npm install @modelcontextprotocol/sdk zod
npm install -D typescript vitest @types/node
```

- [ ] **Step 3: Create tsconfig.json**

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "Node16",
    "moduleResolution": "Node16",
    "outDir": "dist",
    "rootDir": "src",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "declaration": true,
    "declarationMap": true,
    "sourceMap": true
  },
  "include": ["src"],
  "exclude": ["node_modules", "dist", "tests"]
}
```

- [ ] **Step 4: Create vitest.config.ts**

```typescript
import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    globals: true,
    environment: "node",
  },
});
```

- [ ] **Step 5: Create .gitignore**

```
node_modules/
dist/
*.tsbuildinfo
```

- [ ] **Step 6: Commit**

```bash
git add package.json tsconfig.json vitest.config.ts .gitignore package-lock.json
git commit -m "$(cat <<'EOF'
chore: initialize ost-mcp TypeScript project

Co-Authored-By: spidecode-bot <263227865+spicode-bot@users.noreply.github.com>
EOF
)"
```

---

### Task 2: Create config module

**Files:**
- Create: `src/config.ts`
- Test: `tests/config.test.ts`

- [ ] **Step 1: Write the test**

Create `tests/config.test.ts`:
```typescript
import { describe, it, expect, beforeEach, afterEach } from "vitest";
import { getConfig } from "../src/config.js";

describe("getConfig", () => {
  const originalEnv = process.env;

  beforeEach(() => {
    process.env = { ...originalEnv };
  });

  afterEach(() => {
    process.env = originalEnv;
  });

  it("reads OST_API_URL from environment", () => {
    process.env.OST_API_URL = "https://api.example.com";
    const config = getConfig();
    expect(config.apiUrl).toBe("https://api.example.com");
  });

  it("uses default URL when OST_API_URL is not set", () => {
    delete process.env.OST_API_URL;
    const config = getConfig();
    expect(config.apiUrl).toBe("https://api.opensource-together.com");
  });

  it("strips trailing slash from URL", () => {
    process.env.OST_API_URL = "https://api.example.com/";
    const config = getConfig();
    expect(config.apiUrl).toBe("https://api.example.com");
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npx vitest run tests/config.test.ts`
Expected: FAIL — module not found

- [ ] **Step 3: Write the config module**

Create `src/config.ts`:
```typescript
export interface Config {
  apiUrl: string;
}

const DEFAULT_API_URL = "https://api.opensource-together.com";

export function getConfig(): Config {
  const rawUrl = process.env.OST_API_URL || DEFAULT_API_URL;
  const apiUrl = rawUrl.endsWith("/") ? rawUrl.slice(0, -1) : rawUrl;

  return { apiUrl };
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `npx vitest run tests/config.test.ts`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/config.ts tests/config.test.ts
git commit -m "$(cat <<'EOF'
feat: add config module with OST_API_URL

Co-Authored-By: spidecode-bot <263227865+spicode-bot@users.noreply.github.com>
EOF
)"
```

---

### Task 3: Create HTTP client

**Files:**
- Create: `src/client.ts`
- Create: `src/types.ts`
- Test: `tests/client.test.ts`

- [ ] **Step 1: Write types**

Create `src/types.ts`:
```typescript
export interface Category {
  id: string;
  name: string;
}

export interface Domain {
  id: string;
  name: string;
}

export interface TechStack {
  id: string;
  name: string;
  icon_url: string;
  type: string;
}

export interface Project {
  id: string;
  title: string;
  description: string | null;
  repo_url: string | null;
  published: boolean;
  trending: boolean;
  logo_url: string | null;
  categories: Category[];
  domains: Domain[];
  tech_stacks: TechStack[];
}

export interface SimilarProject {
  id: string;
  title: string;
  description: string | null;
  repo_url: string | null;
  similarity: number;
}

export interface TrendingProject {
  project_id: string;
  stars: number | null;
  last_synced_at: string | null;
}
```

- [ ] **Step 2: Write the test**

Create `tests/client.test.ts`:
```typescript
import { describe, it, expect, vi, beforeEach } from "vitest";
import { OSTClient } from "../src/client.js";

describe("OSTClient", () => {
  let client: OSTClient;

  beforeEach(() => {
    client = new OSTClient("https://api.example.com");
  });

  it("searchProjects calls correct URL with query params", async () => {
    const mockResponse = [{ id: "1", title: "Test" }];
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockResponse),
    });

    const result = await client.searchProjects({ q: "react", limit: 5 });
    expect(result).toEqual(mockResponse);
    expect(fetch).toHaveBeenCalledWith(
      expect.stringContaining("/projects/search?q=react&limit=5")
    );
  });

  it("getProject calls correct URL", async () => {
    const mockProject = { id: "abc", title: "My Project" };
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockProject),
    });

    const result = await client.getProject("abc");
    expect(result).toEqual(mockProject);
  });

  it("throws on non-ok response", async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 404,
      json: () => Promise.resolve({ detail: "Not found" }),
    });

    await expect(client.getProject("bad-id")).rejects.toThrow("Not found");
  });
});
```

- [ ] **Step 3: Run test to verify it fails**

Run: `npx vitest run tests/client.test.ts`
Expected: FAIL

- [ ] **Step 4: Write the client module**

Create `src/client.ts`:
```typescript
import type {
  Category,
  Domain,
  Project,
  SimilarProject,
  TechStack,
  TrendingProject,
} from "./types.js";

export class OSTClient {
  private baseUrl: string;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  private async request<T>(path: string): Promise<T> {
    const response = await fetch(`${this.baseUrl}${path}`);
    if (!response.ok) {
      const body = await response.json().catch(() => ({}));
      throw new Error(
        (body as { detail?: string }).detail ||
          `API error: ${response.status}`
      );
    }
    return response.json() as Promise<T>;
  }

  async searchProjects(params: {
    q: string;
    category?: string;
    domain?: string;
    techstack?: string;
    limit?: number;
  }): Promise<Project[]> {
    const searchParams = new URLSearchParams();
    searchParams.set("q", params.q);
    if (params.category) searchParams.set("category", params.category);
    if (params.domain) searchParams.set("domain", params.domain);
    if (params.techstack) searchParams.set("techstack", params.techstack);
    if (params.limit) searchParams.set("limit", String(params.limit));
    return this.request(`/projects/search?${searchParams}`);
  }

  async getProject(projectId: string): Promise<Project> {
    return this.request(`/projects/${projectId}`);
  }

  async findSimilar(
    projectId: string,
    limit?: number
  ): Promise<SimilarProject[]> {
    const params = limit ? `?limit=${limit}` : "";
    return this.request(`/projects/${projectId}/similar${params}`);
  }

  async getTrending(limit?: number): Promise<TrendingProject[]> {
    const params = limit ? `?limit=${limit}` : "";
    return this.request(`/recommendations/trending${params}`);
  }

  async listCategories(): Promise<Category[]> {
    return this.request("/categories");
  }

  async listDomains(): Promise<Domain[]> {
    return this.request("/domains");
  }

  async listTechStacks(): Promise<TechStack[]> {
    return this.request("/techstacks");
  }
}
```

- [ ] **Step 5: Run test to verify it passes**

Run: `npx vitest run tests/client.test.ts`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add src/types.ts src/client.ts tests/client.test.ts
git commit -m "$(cat <<'EOF'
feat: add OSTClient HTTP wrapper for ost-linker API

Co-Authored-By: spidecode-bot <263227865+spicode-bot@users.noreply.github.com>
EOF
)"
```

---

## Chunk 2: MCP tools

### Task 4: Create MCP server with search_projects tool

**Files:**
- Create: `src/tools/search.ts`
- Create: `src/index.ts`
- Test: `tests/tools/search.test.ts`

- [ ] **Step 1: Write the test**

Create `tests/tools/search.test.ts`:
```typescript
import { describe, it, expect, vi } from "vitest";
import { createSearchTool } from "../src/tools/search.js";
import type { OSTClient } from "../src/client.js";

describe("search_projects tool", () => {
  it("calls client.searchProjects with correct params", async () => {
    const mockClient = {
      searchProjects: vi.fn().mockResolvedValue([
        { id: "1", title: "React App", description: "A react app" },
      ]),
    } as unknown as OSTClient;

    const tool = createSearchTool(mockClient);
    const result = await tool.handler({ q: "react", limit: 5 });

    expect(mockClient.searchProjects).toHaveBeenCalledWith({
      q: "react",
      limit: 5,
    });
    expect(result).toContain("React App");
  });

  it("returns message when no results found", async () => {
    const mockClient = {
      searchProjects: vi.fn().mockResolvedValue([]),
    } as unknown as OSTClient;

    const tool = createSearchTool(mockClient);
    const result = await tool.handler({ q: "nonexistent" });

    expect(result).toContain("No projects found");
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npx vitest run tests/tools/search.test.ts`
Expected: FAIL

- [ ] **Step 3: Write the search tool**

Create `src/tools/search.ts`:
```typescript
import { z } from "zod";
import type { OSTClient } from "../client.js";

export const searchToolSchema = z.object({
  q: z.string().describe("Search query (project title or description)"),
  category: z.string().optional().describe("Filter by category name"),
  domain: z.string().optional().describe("Filter by domain name"),
  techstack: z.string().optional().describe("Filter by tech stack name"),
  limit: z
    .number()
    .min(1)
    .max(50)
    .optional()
    .default(20)
    .describe("Max results (default 20, max 50)"),
});

export function createSearchTool(client: OSTClient) {
  return {
    name: "search_projects",
    description:
      "Search open-source projects by keyword. Optionally filter by category, domain, or tech stack.",
    schema: searchToolSchema,
    handler: async (params: z.infer<typeof searchToolSchema>): Promise<string> => {
      const projects = await client.searchProjects(params);

      if (projects.length === 0) {
        return "No projects found matching your query.";
      }

      return projects
        .map(
          (p) =>
            `**${p.title}** (${p.repo_url || "no URL"})\n${p.description || "No description"}`
        )
        .join("\n\n");
    },
  };
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `npx vitest run tests/tools/search.test.ts`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/tools/search.ts tests/tools/search.test.ts
git commit -m "$(cat <<'EOF'
feat: add search_projects MCP tool

Co-Authored-By: spidecode-bot <263227865+spicode-bot@users.noreply.github.com>
EOF
)"
```

---

### Task 5: Create remaining tools (project, trending, similar, references)

**Files:**
- Create: `src/tools/project.ts`
- Create: `src/tools/trending.ts`
- Create: `src/tools/similar.ts`
- Create: `src/tools/references.ts`
- Test: `tests/tools/project.test.ts`
- Test: `tests/tools/trending.test.ts`
- Test: `tests/tools/similar.test.ts`
- Test: `tests/tools/references.test.ts`

- [ ] **Step 1: Write tests for all tools**

Create `tests/tools/project.test.ts`:
```typescript
import { describe, it, expect, vi } from "vitest";
import { createGetProjectTool } from "../src/tools/project.js";
import type { OSTClient } from "../src/client.js";

describe("get_project tool", () => {
  it("returns formatted project details", async () => {
    const mockClient = {
      getProject: vi.fn().mockResolvedValue({
        id: "1",
        title: "FastAPI",
        description: "Modern Python web framework",
        repo_url: "https://github.com/tiangolo/fastapi",
        categories: [{ id: "c1", name: "Web Development" }],
        domains: [{ id: "d1", name: "Backend" }],
        tech_stacks: [{ id: "t1", name: "Python", type: "LANGUAGE" }],
      }),
    } as unknown as OSTClient;

    const tool = createGetProjectTool(mockClient);
    const result = await tool.handler({ project_id: "1" });

    expect(result).toContain("FastAPI");
    expect(result).toContain("Web Development");
    expect(result).toContain("Python");
  });
});
```

Create `tests/tools/trending.test.ts`:
```typescript
import { describe, it, expect, vi } from "vitest";
import { createTrendingTool } from "../src/tools/trending.js";
import type { OSTClient } from "../src/client.js";

describe("get_trending tool", () => {
  it("returns formatted trending projects", async () => {
    const mockClient = {
      getTrending: vi.fn().mockResolvedValue([
        { project_id: "1", stars: 5000, last_synced_at: "2026-01-01" },
        { project_id: "2", stars: 3000, last_synced_at: "2026-01-01" },
      ]),
    } as unknown as OSTClient;

    const tool = createTrendingTool(mockClient);
    const result = await tool.handler({ limit: 10 });

    expect(result).toContain("5000");
    expect(mockClient.getTrending).toHaveBeenCalledWith(10);
  });
});
```

Create `tests/tools/similar.test.ts`:
```typescript
import { describe, it, expect, vi } from "vitest";
import { createSimilarTool } from "../src/tools/similar.js";
import type { OSTClient } from "../src/client.js";

describe("find_similar tool", () => {
  it("returns similar projects with similarity scores", async () => {
    const mockClient = {
      findSimilar: vi.fn().mockResolvedValue([
        { id: "2", title: "Similar Project", similarity: 0.85 },
      ]),
    } as unknown as OSTClient;

    const tool = createSimilarTool(mockClient);
    const result = await tool.handler({ project_id: "1", limit: 5 });

    expect(result).toContain("Similar Project");
    expect(result).toContain("85");
    expect(mockClient.findSimilar).toHaveBeenCalledWith("1", 5);
  });
});
```

Create `tests/tools/references.test.ts`:
```typescript
import { describe, it, expect, vi } from "vitest";
import { createCategoriesTool, createDomainsTool, createTechStacksTool } from "../src/tools/references.js";
import type { OSTClient } from "../src/client.js";

describe("list_categories tool", () => {
  it("returns formatted categories", async () => {
    const mockClient = {
      listCategories: vi.fn().mockResolvedValue([
        { id: "1", name: "Web Development" },
        { id: "2", name: "Machine Learning" },
      ]),
    } as unknown as OSTClient;

    const tool = createCategoriesTool(mockClient);
    const result = await tool.handler({});

    expect(result).toContain("Web Development");
    expect(result).toContain("Machine Learning");
  });
});

describe("list_domains tool", () => {
  it("returns formatted domains", async () => {
    const mockClient = {
      listDomains: vi.fn().mockResolvedValue([
        { id: "1", name: "Healthcare" },
      ]),
    } as unknown as OSTClient;

    const tool = createDomainsTool(mockClient);
    const result = await tool.handler({});

    expect(result).toContain("Healthcare");
  });
});

describe("list_techstacks tool", () => {
  it("returns formatted tech stacks", async () => {
    const mockClient = {
      listTechStacks: vi.fn().mockResolvedValue([
        { id: "1", name: "Python", type: "LANGUAGE", icon_url: "http://img" },
      ]),
    } as unknown as OSTClient;

    const tool = createTechStacksTool(mockClient);
    const result = await tool.handler({});

    expect(result).toContain("Python");
    expect(result).toContain("LANGUAGE");
  });
});
```

- [ ] **Step 2: Run all tool tests to verify they fail**

Run: `npx vitest run tests/tools/`
Expected: FAIL

- [ ] **Step 3: Write all tool modules**

Create `src/tools/project.ts`:
```typescript
import { z } from "zod";
import type { OSTClient } from "../client.js";

export const getProjectSchema = z.object({
  project_id: z.string().describe("UUID of the project"),
});

export function createGetProjectTool(client: OSTClient) {
  return {
    name: "get_project",
    description: "Get full details of a specific open-source project by ID.",
    schema: getProjectSchema,
    handler: async (params: z.infer<typeof getProjectSchema>): Promise<string> => {
      const p = await client.getProject(params.project_id);

      const categories = p.categories.map((c) => c.name).join(", ") || "None";
      const domains = p.domains.map((d) => d.name).join(", ") || "None";
      const techStacks = p.tech_stacks.map((t) => t.name).join(", ") || "None";

      return [
        `# ${p.title}`,
        p.description || "No description",
        "",
        `**URL:** ${p.repo_url || "N/A"}`,
        `**Categories:** ${categories}`,
        `**Domains:** ${domains}`,
        `**Tech Stacks:** ${techStacks}`,
        `**Published:** ${p.published} | **Trending:** ${p.trending}`,
      ].join("\n");
    },
  };
}
```

Create `src/tools/trending.ts`:
```typescript
import { z } from "zod";
import type { OSTClient } from "../client.js";

export const trendingSchema = z.object({
  limit: z.number().min(1).max(50).optional().default(20).describe("Max results"),
});

export function createTrendingTool(client: OSTClient) {
  return {
    name: "get_trending",
    description: "Get globally trending and popular open-source projects.",
    schema: trendingSchema,
    handler: async (params: z.infer<typeof trendingSchema>): Promise<string> => {
      const projects = await client.getTrending(params.limit);

      if (projects.length === 0) {
        return "No trending projects found.";
      }

      return projects
        .map((p, i) => `${i + 1}. Project ${p.project_id} — ${p.stars ?? "?"} stars`)
        .join("\n");
    },
  };
}
```

Create `src/tools/similar.ts`:
```typescript
import { z } from "zod";
import type { OSTClient } from "../client.js";

export const similarSchema = z.object({
  project_id: z.string().describe("UUID of the project to find similar projects for"),
  limit: z.number().min(1).max(50).optional().default(10).describe("Max results"),
});

export function createSimilarTool(client: OSTClient) {
  return {
    name: "find_similar",
    description:
      "Find projects similar to a given project using AI embeddings (cosine similarity).",
    schema: similarSchema,
    handler: async (params: z.infer<typeof similarSchema>): Promise<string> => {
      const projects = await client.findSimilar(params.project_id, params.limit);

      if (projects.length === 0) {
        return "No similar projects found.";
      }

      return projects
        .map(
          (p) =>
            `**${p.title}** (${Math.round(p.similarity * 100)}% similar)\n${p.repo_url || "no URL"} — ${p.description || "No description"}`
        )
        .join("\n\n");
    },
  };
}
```

Create `src/tools/references.ts`:
```typescript
import { z } from "zod";
import type { OSTClient } from "../client.js";

const emptySchema = z.object({});

export function createCategoriesTool(client: OSTClient) {
  return {
    name: "list_categories",
    description: "List all available project categories.",
    schema: emptySchema,
    handler: async (_params: z.infer<typeof emptySchema>): Promise<string> => {
      const categories = await client.listCategories();
      return categories.map((c) => `- ${c.name}`).join("\n");
    },
  };
}

export function createDomainsTool(client: OSTClient) {
  return {
    name: "list_domains",
    description: "List all available project domains.",
    schema: emptySchema,
    handler: async (_params: z.infer<typeof emptySchema>): Promise<string> => {
      const domains = await client.listDomains();
      return domains.map((d) => `- ${d.name}`).join("\n");
    },
  };
}

export function createTechStacksTool(client: OSTClient) {
  return {
    name: "list_techstacks",
    description: "List all available tech stacks (languages and technologies).",
    schema: emptySchema,
    handler: async (_params: z.infer<typeof emptySchema>): Promise<string> => {
      const stacks = await client.listTechStacks();
      return stacks.map((t) => `- ${t.name} (${t.type})`).join("\n");
    },
  };
}
```

- [ ] **Step 4: Run all tool tests to verify they pass**

Run: `npx vitest run tests/tools/`
Expected: PASS (6+ tests)

- [ ] **Step 5: Commit**

```bash
git add src/tools/ tests/tools/
git commit -m "$(cat <<'EOF'
feat: add project, trending, similar, and reference tools

Co-Authored-By: spidecode-bot <263227865+spicode-bot@users.noreply.github.com>
EOF
)"
```

---

### Task 6: Create MCP server entry point

**Files:**
- Create: `src/index.ts`

- [ ] **Step 1: Write the MCP server**

Create `src/index.ts`:
```typescript
#!/usr/bin/env node

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";

import { OSTClient } from "./client.js";
import { getConfig } from "./config.js";
import { createSearchTool } from "./tools/search.js";
import { createGetProjectTool } from "./tools/project.js";
import { createTrendingTool } from "./tools/trending.js";
import { createSimilarTool } from "./tools/similar.js";
import {
  createCategoriesTool,
  createDomainsTool,
  createTechStacksTool,
} from "./tools/references.js";

const config = getConfig();
const client = new OSTClient(config.apiUrl);

const server = new McpServer({
  name: "ost-mcp",
  version: "0.1.0",
});

// Register all tools
const tools = [
  createSearchTool(client),
  createGetProjectTool(client),
  createTrendingTool(client),
  createSimilarTool(client),
  createCategoriesTool(client),
  createDomainsTool(client),
  createTechStacksTool(client),
];

for (const tool of tools) {
  server.tool(tool.name, tool.description, tool.schema.shape, async (params) => {
    const parsed = tool.schema.parse(params);
    const result = await tool.handler(parsed);
    return { content: [{ type: "text", text: result }] };
  });
}

async function main(): Promise<void> {
  const transport = new StdioServerTransport();
  await server.connect(transport);
}

main().catch(console.error);
```

- [ ] **Step 2: Build the project**

Run: `npm run build`
Expected: Compiles to `dist/` without errors

- [ ] **Step 3: Verify the shebang and binary work**

Run: `node dist/index.js --help 2>&1 || echo "Server started (expected — it uses stdio)"`
Expected: Server starts and waits for stdio input (that's correct behavior)

- [ ] **Step 4: Commit**

```bash
git add src/index.ts
git commit -m "$(cat <<'EOF'
feat: add MCP server entry point with all tools registered

Co-Authored-By: spidecode-bot <263227865+spicode-bot@users.noreply.github.com>
EOF
)"
```

---

## Chunk 3: Distribution and CI

### Task 7: Create CLAUDE.md and .claude/ for ost-mcp

**Files:**
- Create: `CLAUDE.md`
- Create: `.claude/rules/conventions.md`

- [ ] **Step 1: Write CLAUDE.md**

Create `CLAUDE.md`:
```markdown
# CLAUDE.md

## Project Overview

OST MCP is the Model Context Protocol server for [OpenSourceTogether](https://opensource-together.com/). It lets developers discover and explore open-source projects directly from Claude Desktop, IDEs, and other MCP-compatible clients.

It consumes the OST Linker REST API and exposes 7 MCP tools for project search, discovery, and similarity.

## Common Commands

### Development
\`\`\`bash
npm install                    # Install dependencies
npm run build                  # Compile TypeScript
npm run dev                    # Watch mode
npm test                       # Run tests (vitest)
npm run lint                   # Type check (tsc --noEmit)
\`\`\`

### Testing
\`\`\`bash
npx vitest run                 # All tests
npx vitest run tests/tools/    # Tool tests only
npx vitest --watch             # Watch mode
\`\`\`

## Architecture

\`\`\`
User (Claude Desktop/IDE) -> MCP Server (stdio) -> OSTClient (HTTP) -> OST Linker API
\`\`\`

- `src/index.ts` — MCP server entry point, registers all tools
- `src/client.ts` — HTTP client for the OST Linker REST API
- `src/tools/` — One file per MCP tool (or group)
- `src/config.ts` — Reads `OST_API_URL` from env
- `src/types.ts` — Shared TypeScript types

## MCP Tools (v1)

| Tool | Description |
|------|-------------|
| `search_projects` | Search projects by keyword with optional filters |
| `get_project` | Get full project details by ID |
| `get_trending` | Get trending/popular projects |
| `find_similar` | Find similar projects via AI embeddings |
| `list_categories` | List all categories |
| `list_domains` | List all domains |
| `list_techstacks` | List all tech stacks |

## Environment Variables

| Variable | Purpose | Default |
|----------|---------|---------|
| `OST_API_URL` | OST Linker API base URL | `https://api.opensource-together.com` |
\`\`\`
```

- [ ] **Step 2: Write conventions**

Create `.claude/rules/conventions.md`:
```markdown
# Conventions

## Code Style
- TypeScript strict mode
- ESM modules (import/export, .js extensions in imports)
- Vitest for tests
- Zod for schema validation

## Testing
- Co-locate tests in `tests/` mirroring `src/` structure
- Use vitest `describe`/`it` blocks
- Mock the OSTClient in tool tests, mock fetch in client tests

## Git
- Conventional commits: `feat:`, `fix:`, `test:`, `chore:`, `docs:`
- Co-Author: spidecode-bot <263227865+spicode-bot@users.noreply.github.com>
```

- [ ] **Step 3: Commit**

```bash
git add CLAUDE.md .claude/
git commit -m "$(cat <<'EOF'
docs: add CLAUDE.md and conventions for ost-mcp

Co-Authored-By: spidecode-bot <263227865+spicode-bot@users.noreply.github.com>
EOF
)"
```

---

### Task 8: Add CI workflow

**Files:**
- Create: `.github/workflows/ci.yml`

- [ ] **Step 1: Write CI workflow**

Create `.github/workflows/ci.yml`:
```yaml
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  build-and-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: npm
      - run: npm ci
      - run: npm run lint
      - run: npm test
      - run: npm run build
```

- [ ] **Step 2: Commit**

```bash
git add .github/workflows/ci.yml
git commit -m "$(cat <<'EOF'
ci: add build and test workflow

Co-Authored-By: spidecode-bot <263227865+spicode-bot@users.noreply.github.com>
EOF
)"
```

---

### Task 9: Final verification

- [ ] **Step 1: Run full build**

Run: `npm run build`
Expected: No errors

- [ ] **Step 2: Run all tests**

Run: `npm test`
Expected: All tests pass

- [ ] **Step 3: Run type check**

Run: `npm run lint`
Expected: No errors

- [ ] **Step 4: Test npx dry run**

Run: `node dist/index.js` (will hang waiting for stdio — that's correct)
Expected: No crash, no errors on stderr

- [ ] **Step 5: Commit any fixes**

```bash
git add -u
git commit -m "$(cat <<'EOF'
fix: resolve lint and build issues

Co-Authored-By: spidecode-bot <263227865+spicode-bot@users.noreply.github.com>
EOF
)"
```
