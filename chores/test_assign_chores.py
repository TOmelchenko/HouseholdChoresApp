"""Tests for the assign_chores management command."""

from datetime import timedelta

from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from .models import Assignment, Chore, Household, Roommate


class AssignChoresCommandTest(TestCase):
    def setUp(self):
        # This app ships a data migration (0002_seed_predefined_chores) that
        # seeds a handful of Chore rows. Clear them so each test controls
        # exactly which chores exist and can make simple assertions about
        # Assignment counts, independent of that seed data.
        Chore.objects.all().delete()

        self.today = timezone.localdate()
        self.household = Household.objects.create()
        self.alice = Roommate.objects.create(household=self.household, name="Alice")
        self.bob = Roommate.objects.create(household=self.household, name="Bob")
        self.chore = Chore.objects.create(name="Take out trash", frequency_days=7)

    def test_no_prior_assignment_creates_one_due_today(self):
        call_command("assign_chores")

        self.assertEqual(Assignment.objects.count(), 1)
        assignment = Assignment.objects.get()
        self.assertEqual(assignment.chore, self.chore)
        self.assertEqual(assignment.roommate, self.alice)
        self.assertEqual(assignment.due_date, self.today)
        self.assertIsNone(assignment.completed_at)

    def test_running_twice_same_day_is_idempotent(self):
        call_command("assign_chores")
        call_command("assign_chores")

        self.assertEqual(Assignment.objects.count(), 1)

    def test_incomplete_most_recent_assignment_is_not_due_regardless_of_age(self):
        Assignment.objects.create(
            chore=self.chore,
            roommate=self.alice,
            due_date=self.today - timedelta(days=30),
            completed_at=None,
        )

        call_command("assign_chores")

        self.assertEqual(Assignment.objects.count(), 1)

    def test_completed_assignment_past_frequency_window_creates_new_one(self):
        old_due = self.today - timedelta(days=8)
        Assignment.objects.create(
            chore=self.chore,
            roommate=self.alice,
            due_date=old_due,
            completed_at=timezone.now(),
        )

        call_command("assign_chores")

        self.assertEqual(Assignment.objects.count(), 2)
        new_assignment = Assignment.objects.order_by("id").last()
        self.assertEqual(new_assignment.due_date, self.today)
        self.assertIsNone(new_assignment.completed_at)
        # Round robin: Alice was assigned last, so Bob is next.
        self.assertEqual(new_assignment.roommate, self.bob)

    def test_completed_assignment_within_frequency_window_is_not_due(self):
        recent_due = self.today - timedelta(days=1)
        Assignment.objects.create(
            chore=self.chore,
            roommate=self.alice,
            due_date=recent_due,
            completed_at=timezone.now(),
        )

        call_command("assign_chores")

        self.assertEqual(Assignment.objects.count(), 1)

    def test_new_assignment_due_date_is_today_not_theoretical_next_due(self):
        # Chore wasn't run for a while: completed assignment was due 20 days
        # ago (frequency is 7 days), so next_due would theoretically be 13
        # days ago, but the new Assignment should be dated today.
        old_due = self.today - timedelta(days=20)
        Assignment.objects.create(
            chore=self.chore,
            roommate=self.alice,
            due_date=old_due,
            completed_at=timezone.now(),
        )

        call_command("assign_chores")

        new_assignment = Assignment.objects.order_by("id").last()
        self.assertEqual(new_assignment.due_date, self.today)

    def test_household_with_zero_roommates_is_skipped_without_crashing(self):
        empty_household = Household.objects.create()

        call_command("assign_chores")

        self.assertFalse(
            Assignment.objects.filter(roommate__household=empty_household).exists()
        )
        # Sanity: the populated household still got its assignment.
        self.assertEqual(Assignment.objects.count(), 1)

    def test_new_chore_added_later_is_picked_up_on_next_run(self):
        call_command("assign_chores")
        self.assertEqual(Assignment.objects.count(), 1)

        new_chore = Chore.objects.create(name="Vacuum", frequency_days=3)
        call_command("assign_chores")

        self.assertEqual(Assignment.objects.count(), 2)
        self.assertTrue(Assignment.objects.filter(chore=new_chore).exists())

    def test_two_households_with_same_chore_evaluated_independently(self):
        household_b = Household.objects.create()
        carol = Roommate.objects.create(household=household_b, name="Carol")

        # Household A: completed and due again.
        Assignment.objects.create(
            chore=self.chore,
            roommate=self.alice,
            due_date=self.today - timedelta(days=8),
            completed_at=timezone.now(),
        )
        # Household B: still incomplete.
        Assignment.objects.create(
            chore=self.chore,
            roommate=carol,
            due_date=self.today - timedelta(days=8),
            completed_at=None,
        )

        call_command("assign_chores")

        # Household A got a new assignment (2 total: old + new).
        self.assertEqual(
            Assignment.objects.filter(roommate__household=self.household).count(), 2
        )
        # Household B's incomplete assignment was left untouched.
        self.assertEqual(
            Assignment.objects.filter(roommate__household=household_b).count(), 1
        )

    def test_chore_never_assigned_in_household_does_not_crash(self):
        # Chore has history in a *different* household only.
        other_household = Household.objects.create()
        dave = Roommate.objects.create(household=other_household, name="Dave")
        Assignment.objects.create(
            chore=self.chore,
            roommate=dave,
            due_date=self.today,
            completed_at=None,
        )

        call_command("assign_chores")

        # self.household still gets a fresh assignment for this chore,
        # independent of other_household's history.
        self.assertTrue(
            Assignment.objects.filter(
                chore=self.chore, roommate__household=self.household
            ).exists()
        )

    def test_summary_output_reports_created_count(self):
        out = []

        class Recorder:
            def write(self, msg):
                out.append(str(msg))

        call_command("assign_chores", stdout=Recorder())

        self.assertTrue(any("1" in line for line in out))

    def test_help_text_mentions_single_run_and_issue_12(self):
        from chores.management.commands.assign_chores import Command

        help_text = Command.help
        self.assertIn("single run", help_text.lower())
        self.assertIn("12", help_text)
