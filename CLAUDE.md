# HouseholdChoresApp

A mobile app that fairly distributes recurring household chores among roommates. No accounts, no dashboards — just a join code and a list of what to do today.

## Tech Stack

- **Mobile:** Expo (React Native, TypeScript)
- **Database & API:** Supabase (Postgres + auto-generated REST)
- **Background jobs:** Supabase Edge Functions + pg_cron

## Key Docs

- `_docs/plan.md` — MVP specification and user flow
- `_docs/tasks.md` — implementation backlog
- GitHub issues mirror each task in the backlog

## Project Structure

```
src/
  lib/supabase.ts     # Supabase client (single export)
  screens/            # One file per screen
supabase/
  migrations/         # SQL schema files
  seeds/              # SQL seed data
  functions/          # Edge Functions
```

## Commands

```bash
npm test        # Run Jest tests
npx expo start  # Start the dev server
```

## Conventions

- Each screen is self-contained in `src/screens/`
- All Supabase access goes through `src/lib/supabase.ts`
- Rotation logic lives as a pure function with unit tests
- No confirmation dialogs — actions are immediate
- No custom chores, no effort scores, no swap flows (out of scope for MVP)
