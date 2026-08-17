# Suomi-Master

A mobile-first Finnish utility app for Russian-speaking and Finnish residents of the Kokkola/Kronoby region. Features AI vehicle diagnostics, P2P neighborhood tool rental, a car maintenance log, outdoor/fishing conditions, and multilingual support (RU/EN/FI).

## Run & Operate

- `pnpm --filter @workspace/suomi-master run dev` — run the frontend (port from env)
- `pnpm --filter @workspace/api-server run dev` — run the API server (port 8080)
- `pnpm run typecheck` — full typecheck across all packages
- `pnpm --filter @workspace/api-spec run codegen` — regenerate API hooks and Zod schemas from the OpenAPI spec
- `pnpm --filter @workspace/db run push` — push DB schema changes (dev only)
- Required env: `DATABASE_URL` — Postgres connection string

## Stack

- pnpm workspaces, Node.js 24, TypeScript 5.9
- Frontend: React + Vite, Tailwind CSS, Framer Motion, Wouter
- API: Express 5
- Auth: Replit Auth (OIDC/PKCE) via `@workspace/replit-auth-web`
- DB: PostgreSQL + Drizzle ORM
- Validation: Zod (`zod/v4`), `drizzle-zod`
- API codegen: Orval (from OpenAPI spec)
- Build: esbuild (CJS bundle)

## Where things live

- `lib/api-spec/openapi.yaml` — single source of truth for all API contracts
- `lib/db/src/schema/app.ts` — rentals, comments, garage logs, diagnose history, notifications
- `lib/db/src/schema/auth.ts` — Replit Auth sessions and users
- `artifacts/api-server/src/routes/` — Express route handlers (diagnose, rentals, garage, weather, notifications, auth)
- `artifacts/suomi-master/src/` — React frontend (5-tab mobile app)

## Architecture decisions

- **Replit Auth** used instead of custom JWT/bcrypt to match platform conventions
- **Keyword-based diagnosis** engine implemented in `routes/diagnose.ts` — no external AI dependency required; can be upgraded to real AI later
- **Seasonal weather simulation** in `routes/weather.ts` — approximates Gulf of Bothnia conditions by month; upgrade with FMI open data API call
- **Dark-theme-only** frontend — no light mode toggle, intentional UX decision for the target audience
- **Language context** (`useLanguage` hook) powers all RU/EN/FI translations without page reloads

## Product

- **Workshop tab**: AI-style car/equipment diagnostics with OBD2 code support, severity rating, and Finnish auto parts store links
- **Garage tab**: Personal car maintenance log (requires login), Finnish katsastus checklist, Ekorosk recycling info
- **Rentals tab**: P2P tool sharing listings with inline chat, phone/WhatsApp contact links
- **Outdoors tab**: Fishing bite index, weather conditions, Finnish fishing spots, foraging tips by season
- **Profile tab**: Replit Auth login/logout, notification inbox

## User preferences

_Populate as needed._

## Gotchas

- OpenAPI `format: email` and `format: uri` cause `zod.email()` / `zod.url()` generation which is incompatible with Zod v3 — avoid these formats in the spec
- `type: integer` causes `zod.int()` generation, also incompatible with Zod v3 — use `type: number` instead
- After any spec change, run `pnpm --filter @workspace/api-spec run codegen` before building
- Zod v3 is used workspace-wide — the spec must avoid OpenAPI 3.1 formats that produce v4-only validators

## Pointers

- See the `pnpm-workspace` skill for workspace structure, TypeScript setup, and package details
- See the `replit-auth` skill for auth architecture details
