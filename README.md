# Household Chores App

A shared household chores management app that fairly distributes recurring chores among roommates — without accounts, dashboards, or complexity.

## What It Does

- A household is created automatically when the first roommate opens the app
- Other roommates join using a shared household code and their name
- Entering a name that already exists in the household resumes that
  roommate's session, so anyone can get back to their own chores from a new
  device or browser without losing their identity
- Predefined chores are automatically assigned using a round-robin rotation
- Each roommate sees only their own chores and due dates
- Chores are completed with a single click, and can be undone within 5 minutes

## Key Features

- **No accounts or passwords** — just a shared household code and your name
- **Resume by name** — re-entering your name on the join form logs you back
  in as yourself instead of creating a duplicate roommate
- **Fair rotation** — chores are distributed in strict round-robin order
- **Overdue handling** — missed chores stay assigned and carry over

## Out of Scope (MVP)

- Push notifications / reminders
- Custom chores
- Effort scores
- Chore swapping
- Vacation mode
- Leaderboards or gamification
- Household dashboard
- Approval workflow for joining

## Docs

- [`_docs/how-to-use.md`](_docs/how-to-use.md) — quick start guide for running and using the app
- [`_docs/plan.md`](_docs/plan.md) — full MVP specification
