# SEO Visibility Agent

An AI-powered local SEO visibility optimization agent built on [Cloudflare's Agents SDK](https://developers.cloudflare.com/agents/). This application helps local businesses understand and improve their search visibility through an interactive chat interface.

## Architecture & Cloudflare Components

| Requirement | Implementation |
|---|---|
| **LLM** | [Workers AI](https://developers.cloudflare.com/workers-ai/) — GLM 4.7 Flash model, no API keys needed |
| **Workflow / Coordination** | [Durable Objects](https://developers.cloudflare.com/durable-objects/) — `ChatAgent` class with multi-step SEO analysis pipeline and tool orchestration |
| **User Input (Chat)** | React chat UI via [`useAgentChat`](https://developers.cloudflare.com/agents/api-reference/chat-agents/) hook over WebSocket, with human-in-the-loop approval |
| **Memory / State** | Durable Object SQLite for message persistence + synced agent state for business profile and analysis history |

## How It Works

The agent implements a **3-step SEO optimization pipeline** ported from a Python multi-agent system:

### Step 1 — Discovery & Analysis
The user describes their business and asks about search visibility. The agent saves the business profile to persistent state, then runs `analyzeLocalSearch` — a tool that internally calls Workers AI to simulate realistic local search rankings and diagnose where the business stands vs. competitors.

### Step 2 — Diagnosis & Planning
The agent explains ranking positions using five local-search factors (Relevance, Proximity, Prominence, Trust, Freshness) and categorizes evidence into Brand / Social / Earned buckets.

### Step 3 — Execution & Content Generation
Server-side tools generate actionable SEO materials:
- **Schema markup** — JSON-LD structured data (LocalBusiness, BarOrPub, Restaurant, etc.)
- **Meta tags** — Title, description, Open Graph, geo tags per page type
- **Citation list** — Prioritized directory submission list with NAP consistency guidance

### Key Features

- **Human-in-the-loop**: The `analyzeLocalSearch` tool requires user approval before running (demonstrates the `needsApproval` pattern)
- **Client-side tools**: `getUserLocation` runs in the browser via the Geolocation API and returns coordinates to the agent
- **State persistence**: Business profile and analysis history survive page reloads, server restarts, and hibernation
- **Streaming responses**: Real-time AI response streaming with resumable streams on disconnect

## Tools Available to the Agent

| Tool | Type | Description |
|---|---|---|
| `saveBusinessProfile` | Server (auto) | Saves business details to Durable Object state |
| `getBusinessProfile` | Server (auto) | Retrieves the saved business profile |
| `analyzeLocalSearch` | Server (approval) | Runs multi-step AI analysis pipeline — simulates local search rankings |
| `generateSchemaMarkup` | Server (auto) | Generates JSON-LD structured data markup |
| `generateMetaTags` | Server (auto) | Generates SEO meta tags for any page type |
| `generateCitationList` | Server (auto) | Generates prioritized directory submission list |
| `getUserLocation` | Client-side | Gets browser geolocation for location-aware analysis |

## Getting Started

### Prerequisites

- A [Cloudflare account](https://dash.cloudflare.com/sign-up) (free tier works)
- Node.js 20.19+ or 22.12+

### Local Development

```bash
# Install dependencies
npm install

# Generate types
npx wrangler types

# Start dev server
npm run dev
```

Open http://localhost:5173 and start chatting. Try:
1. "My business is Wicked Willy's at 149 Bleecker St, New York, NY 10012. We're a bar."
2. "Why don't I show up when people search 'best bars near Bleecker Street'?"
3. "Generate JSON-LD schema markup for my business"
4. "What directories should I list my bar on?"

### Deploy to Cloudflare

```bash
npm run deploy
```

Your agent will be live on Cloudflare's global network. Messages persist in SQLite, streams resume on disconnect, and the agent hibernates when idle.

## Tech Stack

- **Runtime**: Cloudflare Workers + Durable Objects
- **AI**: Workers AI (GLM 4.7 Flash) via [Vercel AI SDK](https://sdk.vercel.ai/)
- **Frontend**: React 19 + [Kumo UI](https://www.npmjs.com/package/@cloudflare/kumo) + Tailwind CSS 4
- **Agent SDK**: [`agents`](https://www.npmjs.com/package/agents) + [`@cloudflare/ai-chat`](https://www.npmjs.com/package/@cloudflare/ai-chat)
- **Build**: Vite 7 + `@cloudflare/vite-plugin`

## Project Structure

```
cloudflare-app/
├── src/
│   ├── server.ts      # ChatAgent with SEO tools (Durable Object)
│   ├── client.tsx      # React entry point
│   ├── app.tsx         # Chat UI components
│   └── styles.css      # Tailwind + Kumo styles
├── index.html          # HTML shell
├── wrangler.jsonc      # Cloudflare Worker config
├── vite.config.ts      # Vite + Cloudflare plugin
├── tsconfig.json       # TypeScript config
└── env.d.ts            # Generated Cloudflare types
```
