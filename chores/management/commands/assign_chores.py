"""Assignment scheduler: creates due Assignment rows for every household/chore.

This command performs a single run. It does not schedule itself, and it is
not a cron job or daemon: it must be invoked by something else (manually, a
CI job, or an OS-level scheduler) each time assignments should be refreshed.
Registering it to run on a recurring schedule (cron, systemd timer,
django-crontab, Heroku Scheduler, etc.) is tracked separately in issue #12
and is explicitly out of scope here.
"""

from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from chores.models import Assignment, Chore, Household
from chores.rotation import next_assignee


class Command(BaseCommand):
    help = (
        "Create due Assignment rows for every household/chore pair, using "
        "round-robin rotation. This command performs a single run; it does "
        "not schedule itself. Recurring invocation (cron/systemd timer/"
        "hosting scheduler) is tracked separately in issue #12."
    )

    def handle(self, *args, **options):
        today = timezone.localdate()
        created_count = 0

        chores = list(Chore.objects.all())

        for household in Household.objects.all():
            roommate_ids = list(
                household.roommates.order_by("id").values_list("id", flat=True)
            )
            if not roommate_ids:
                # No roommates: skip entirely, never call next_assignee with
                # an empty roommate_ids list (it would raise ValueError).
                continue

            for chore in chores:
                most_recent = (
                    Assignment.objects.filter(
                        chore=chore, roommate__household=household
                    )
                    .order_by("due_date", "id")
                    .last()
                )

                is_due = False
                if most_recent is None:
                    is_due = True
                elif most_recent.completed_at is None:
                    is_due = False
                else:
                    next_due = most_recent.due_date + timedelta(
                        days=chore.frequency_days
                    )
                    is_due = today >= next_due

                if not is_due:
                    continue

                history = list(
                    Assignment.objects.filter(
                        chore=chore, roommate__household=household
                    )
                    .order_by("due_date", "id")
                    .values_list("roommate_id", flat=True)
                )

                roommate_id = next_assignee(roommate_ids, history)

                Assignment.objects.create(
                    chore=chore,
                    roommate_id=roommate_id,
                    due_date=today,
                    completed_at=None,
                )
                created_count += 1

        self.stdout.write(
            self.style.SUCCESS(f"Created {created_count} assignment(s).")
        )
