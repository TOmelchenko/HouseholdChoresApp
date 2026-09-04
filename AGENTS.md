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

Conventions

- All models live in `chores/models.py`
- Views are function-based unless a class-based view is clearly simpler
- Templates live in `chores/templates/chores/`
- Rotation logic lives as a pure function in `chores/rotation.py` with unit tests
- No confirmation dialogs — actions are immediate
- No custom chores, no effort scores, no swap flows (out of scope for MVP)
- Session-based household identity (no user accounts)
