# How to Use

## 1. Start the app

With Docker:

```bash
docker compose up
```

Or directly:

```bash
python manage.py migrate
python manage.py runserver
```

Migrations already seed the predefined chores (Take out trash, Vacuum, Clean bathroom, Deep clean kitchen).

Open `http://localhost:8000/` in a browser.

## 2. Create a household

The first person to use the app clicks **Create household**, enters their name, and gets a join code shown on screen. This also sets their session, so they're immediately recognized as that roommate going forward in that browser.

## 3. Others join

Everyone else clicks **Join household**, enters the code and their name.

- **New name** → creates a new roommate and joins the household.
- **Name that already exists in that household** (case-insensitive, whitespace-trimmed) → resumes that roommate's existing session instead of creating a duplicate. This is how you get back to your own chores from a different browser, device, or after clearing cookies — just enter the household code and the same name again.

Two different people should not use the same name in one household — whoever types it resumes the same identity and would see that person's chores.

## 4. Assign chores

Chores aren't assigned in real time. Run the scheduler (by hand, or on the cron schedule documented in `AGENTS.md`):

```bash
python manage.py assign_chores
```

This checks every household's chores against due dates and assignment history, and creates new assignments using round-robin. Note: on a chore's very first-ever assignment there's no rotation history yet, so it goes to the first roommate in the household — it isn't spread across everyone on day one, only on subsequent rotations.

## 5. Use My Chores

Once logged in, `/` redirects to `/chores/`, showing:

- Your incomplete chores, soonest-due first, with an "Overdue" indicator for anything past its due date.
- A **Done** button per chore — no confirmation, it completes immediately.
- A "Recently completed" section for anything you finished in the last 5 minutes, with an **Undo** button. After 5 minutes, undo is no longer available.
