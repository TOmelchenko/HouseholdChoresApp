# Backlog

## 1. Project setup
Goal: Create a Django project with a passing test.
Description: Initialise a new Django project (`household`) and app (`chores`) using `django-admin` and `manage.py`. Confirm the default test runner works by writing one smoke test that asserts `True`. Confirm the test suite runs green with `python manage.py test`.

## 2. Database schema
Goal: Define the Django models for the app.
Description: Create four models in `chores/models.py`: `Household`, `Roommate`, `Chore`, and `Assignment`. Each model should have the fields needed to support the MVP user flow (see plan.md). Run and commit the migrations.

## 3. Seed predefined chores
Goal: Populate the database with the initial list of predefined chores.
Description: Write a data migration (or management command) that inserts a set of predefined chores, each with a name and a frequency in days (e.g. "Take out trash", 1; "Vacuum", 7; "Clean bathroom", 7; "Deep clean kitchen", 14). Commit the migration file.

## 4. Create household view
Goal: Let the first roommate create a household and see the join code.
Description: Build a view and template that creates a new `Household` row on submit and displays the generated join code in large, readable text. Save the household ID and roommate ID to the Django session so the app remembers them across requests. No login or confirmation step.

## 5. Join household view
Goal: Let a roommate join an existing household by entering a code.
Description: Build a view with a form for the household code and the roommate's name. On submit, look up the household by code, create a new `Roommate` row, and persist the household ID and roommate ID to the session. Show a clear error if the code is not found.

## 6. Onboarding routing
Goal: Route the user to the correct view on first visit.
Description: On every request, check the session for a persisted household ID. If one exists, redirect to the main chores view. If not, show a landing page with links to "Create household" and "Join household". This wires together the views from tasks 4 and 5.

## 7. Round-robin rotation function
Goal: Implement the core chore assignment algorithm as a pure function.
Description: Write a Python function in `chores/rotation.py` that takes a list of roommate IDs and the assignment history for a chore, and returns the ID of the roommate who should be assigned next. The function should follow strict round-robin order. Cover it with unit tests for edge cases: single roommate, first-ever assignment, and full rotation cycle.

## 8. Assignment scheduler
Goal: Automatically create new chore assignments on a daily schedule.
Description: Write a Django management command (`python manage.py assign_chores`) that queries all chores, checks which ones are due today based on their frequency and last assignment date, and creates new `Assignment` rows using the round-robin function from task 7. Register the command as a daily cron job. Missed (overdue) assignments are left as-is and not reassigned.

## 9. My chores view
Goal: Show the current roommate their assigned chores.
Description: Build the main view and template that fetches all incomplete assignments for the current roommate and displays them as a list. Each row shows the chore name, due date, and a visual overdue indicator if the due date is in the past. This is a read-only view; the complete action is added in task 10.

## 10. Complete a chore
Goal: Let a roommate mark a chore as done with one click.
Description: Add a button to each chore row on the main view that POSTs to a completion endpoint, which sets `completed_at` on the `Assignment` row. The row should disappear from the list immediately (redirect after POST or minimal JS). No confirmation dialog. Write a test for the completion view.
