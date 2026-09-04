Key Docs

- `_docs/process.md` - how work is organized
- `_docs/tasks.md` — implementation backlog
- GitHub issues mirror each task in the backlog

Project Structure

```
manage.py
requirements.txt
chores/              # main Django app
  models.py
  views.py
  urls.py
  templates/chores/
  tests.py
household/           # Django project settings
  settings.py
  urls.py
  wsgi.py
```

Commands

```bash
python manage.py test   # Run Django tests
python manage.py runserver  # Start the dev server
```

Scheduling `assign_chores` with cron

`assign_chores` (see `_docs/tasks.md`) is run daily via the host's OS-level
`cron`, not a Python-based scheduler — no new dependency required.

Install it with `crontab -e`, then paste in this line (replace the two
`/path/to/...` placeholders with the actual project root and virtualenv
paths):

```
0 3 * * * cd /path/to/HouseholdChoresApp && /path/to/venv/bin/python manage.py assign_chores >> /path/to/HouseholdChoresApp/logs/assign_chores.log 2>&1
```

- `cd`s into the project root first so any relative-path assumptions in
  `manage.py` resolve correctly.
- Calls the project's virtualenv Python interpreter directly (not a bare
  `python`), since cron's `PATH` differs from an interactive login shell's.
- Redirects both stdout and stderr to a log file with `>> ... 2>&1`, so a
  failed run's traceback lands in the file instead of cron's default
  local-mail-spool behavior (which nobody monitors on this project).
- The `logs/` directory must already exist before the first run — `>>`
  will not create missing directories, so `mkdir -p /path/to/HouseholdChoresApp/logs`
  once beforehand.

Conventions

- All models live in `chores/models.py`
- Views are function-based unless a class-based view is clearly simpler
- Templates live in `chores/templates/chores/`
- Rotation logic lives as a pure function in `chores/rotation.py` with unit tests
- No confirmation dialogs — actions are immediate
- No custom chores, no effort scores, no swap flows (out of scope for MVP)
- Session-based household identity (no user accounts)

Rules

- Dependencies are added in `pyproject.toml`. Do not add one without
  asking