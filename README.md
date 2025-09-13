# Aura — “Lovable.dev for COOs” (v0.1)

Natural‑language → operations. Type what you want; Aura scaffolds Slack channels, ClickUp/Notion structures, dashboards, and recurring ops rituals.

---

## Monorepo Layout

```
aura-coo/
  apps/
    web/     # Next.js App Router UI (Tailwind + shared UI pkg)
    api/     # Express API (OpenAI stub, Slack command, planning endpoint)
  packages/
    ai/      # Prompt templates + planner (NL → structured ops plan)
    ui/      # Shared React components
    utils/   # Shared helpers
    db/      # Prisma schema + PrismaClient
```

## Quickstart

**Prereqs**: Node 20+, npm 10+, Postgres (or Supabase).

```bash
# 1) Clone + install
npm i -g corepack && corepack enable npm
npm install

# 2) Env
cp .env.example .env

# 3) DB (local Postgres dev ok)
# Set DATABASE_URL in .env
npm run --workspace packages/db prisma:generate
npm run --workspace packages/db prisma:migrate

# 4) Dev (runs web + api)
npm run dev
# web: http://localhost:3000
# api: http://localhost:4000
```

## Minimal Feature Walkthrough (MVP)

1. Open `http://localhost:3000` → use the “Planner” form.
2. Enter: `Set a weekly ops check‑in with finance and logistics; track SLA and stockouts.`
3. The web app POSTs to `API /ai/plan` → `packages/ai` returns a structured plan (stubbed).
4. The plan renders as a basic COO dashboard (tasks + KPIs).

## Integrations (stubs wired)

- **OpenAI**: Use `OPENAI_API_KEY` to improve the planner quality.
- **Slack**: `/slack/command` route verifies signatures and echoes a draft “ops ritual”. Wire a slash command to test (`/aura plan …`).
- **Supabase** (optional): Starter client in `apps/web/lib/supabaseClient.ts` if you want auth/storage quickly.

## Scripts

- `npm run dev` – run all apps in dev via Turborepo
- `npm run build` – build all
- `npm run lint` – placeholder (extend per app)
- `npm run --workspace packages/db prisma:studio` – open Prisma Studio

## Notes

- Keep models minimal; extend `packages/db/prisma/schema.prisma` as you learn from clients.
- Treat `packages/ai` as the product brain. Keep planner testable and deterministic where possible.
- Ship **templates** (playbooks) next: weekly check‑in, incident response, month‑end close, vendor ping, etc.

---

**Vision**: Aura Agents that keep the company on rails—recurring rituals, checklists, KPI nudges—so the COO never has to “set it up” again.
