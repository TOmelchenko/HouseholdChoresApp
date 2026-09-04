# Household Chores App

A shared household chores management app that fairly distributes recurring chores among roommates — without accounts, dashboards, or complexity.

## What It Does

- A household is created automatically when the first roommate opens the app
- Other roommates join using a shared household code
- Predefined chores are automatically assigned using a rotation that balances both **number of turns** and **total effort**
- Each roommate sees only their own chores and due dates
- Chores are completed with a single click

## Key Features

- **No accounts or login** — just a shared household code
- **Fair rotation** — chores are distributed by effort score, not just count
- **Overdue handling** — missed chores stay assigned and carry over
- **Chore swapping** — roommates can swap chores with mutual approval
- **Vacation mode** — a roommate's chores are temporarily redistributed while they're away

## Chore Effort Scores

Each predefined chore has a default effort score that roommates can adjust:

| Chore | Effort |
|---|---:|
| Take out trash | 1 |
| Vacuum | 2 |
| Clean bathroom | 4 |
| Deep clean kitchen | 5 |

## Out of Scope (MVP)

- Push notifications / reminders
- Custom chores
- Leaderboards or gamification
- Household dashboard
- Approval workflow for joining

## Docs

See [`_docs/shared-household-chores-mvp-specification.md`](_docs/shared-household-chores-mvp-specification.md) for the full MVP specification.
