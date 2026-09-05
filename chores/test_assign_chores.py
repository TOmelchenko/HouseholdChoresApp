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
        new_assignment = Assignment.objects.get(chore=new_chore)
        # Vacuum sorts to index 1 (Chore.objects.order_by("id")) after
        # "Take out trash" (index 0), which already has real history from
        # the first call_command above. Its own real history is still
        # empty, so per the first-round distribution rule its first-ever
        # assignment resolves to roommate_ids[1 % 2] == Bob, not Alice
        # (the pre-#19 behavior of always landing on roommate_ids[0]).
        self.assertEqual(new_assignment.roommate, self.bob)

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

    def test_first_round_distributes_across_roommates_with_wraparound(self):
        # 3 roommates, ids in order [alice, bob, carol]. self.chore ("Take
        # out trash") already exists from setUp; add a 3rd roommate and 3
        # more chores (4 chores total, ordered A, B, C, D by id).
        carol = Roommate.objects.create(household=self.household, name="Carol")
        chore_b = Chore.objects.create(name="B", frequency_days=7)
        chore_c = Chore.objects.create(name="C", frequency_days=7)
        chore_d = Chore.objects.create(name="D", frequency_days=7)

        call_command("assign_chores")

        self.assertEqual(Assignment.objects.count(), 4)
        self.assertEqual(
            Assignment.objects.get(chore=self.chore).roommate, self.alice
        )
        self.assertEqual(Assignment.objects.get(chore=chore_b).roommate, self.bob)
        self.assertEqual(Assignment.objects.get(chore=chore_c).roommate, carol)
        # index 3 wraps: 3 % 3 == 0 -> back to alice.
        self.assertEqual(Assignment.objects.get(chore=chore_d).roommate, self.alice)

    def test_single_roommate_household_always_assigns_that_roommate(self):
        # Remove Bob so this household has exactly one roommate.
        self.bob.delete()
        chore_b = Chore.objects.create(name="B", frequency_days=7)
        chore_c = Chore.objects.create(name="C", frequency_days=7)

        call_command("assign_chores")

        self.assertEqual(Assignment.objects.count(), 3)
        for chore in (self.chore, chore_b, chore_c):
            self.assertEqual(
                Assignment.objects.get(chore=chore).roommate, self.alice
            )

    def test_two_households_offset_independently(self):
        # Household A (self.household): roommates [alice, bob].
        # Household B: roommates [dave, erin, frank].
        household_b = Household.objects.create()
        dave = Roommate.objects.create(household=household_b, name="Dave")
        erin = Roommate.objects.create(household=household_b, name="Erin")
        frank = Roommate.objects.create(household=household_b, name="Frank")

        # Global chore ordering: self.chore (index 0), a filler chore
        # (index 1), then chore_index_2 (index 2) — the one we assert on.
        Chore.objects.create(name="Filler", frequency_days=7)
        chore_index_2 = Chore.objects.create(name="Sweep", frequency_days=7)

        call_command("assign_chores")

        # Household A: real history empty, i=2>0, seed=[roommate_ids[(2-1)%2]]
        # = [roommate_ids[1]] = [bob]; next_assignee(ids, [bob]) advances
        # past bob and wraps back to roommate_ids[0] = alice. (Equivalently:
        # roommate_ids[i % len(roommate_ids)] = roommate_ids[2 % 2] = alice.)
        self.assertEqual(
            Assignment.objects.get(
                chore=chore_index_2, roommate__household=self.household
            ).roommate,
            self.alice,
        )
        # Household B: index 2 -> roommate_ids[2 % 3] = roommate_ids[2] = frank.
        self.assertEqual(
            Assignment.objects.get(
                chore=chore_index_2, roommate__household=household_b
            ).roommate,
            frank,
        )
        # Sanity: household B's own roommate count/order never affects
        # household A's result, and vice versa (asserted implicitly above
        # since each computed independently from its own roommate_ids).

    def test_index_based_offset_is_stable_regardless_of_due_date_timing(self):
        # Day 1: only 2 chores exist yet (index 0 and 1). They're due and
        # get assigned to roommate_ids[0] and roommate_ids[1] respectively.
        chore_b = Chore.objects.create(name="B", frequency_days=7)
        call_command("assign_chores")

        self.assertEqual(
            Assignment.objects.get(chore=self.chore).roommate, self.alice
        )
        self.assertEqual(Assignment.objects.get(chore=chore_b).roommate, self.bob)

        # Days later: chores at indices 2 and 3 are added to the global
        # ordering (this household has no real assignment history for any
        # of them), followed by the chore we care about at index 4.
        Chore.objects.create(name="C", frequency_days=7)
        Chore.objects.create(name="D", frequency_days=7)
        chore_at_index_4 = Chore.objects.create(name="E", frequency_days=7)

        call_command("assign_chores")

        # Chore at index 4's first-ever assignment uses i == 4 ->
        # roommate_ids[4 % 2] == roommate_ids[0] == alice — the same
        # offset it would have gotten had it been due back on day 1,
        # regardless of indices 2 and 3 having no real assignment either.
        self.assertEqual(
            Assignment.objects.get(chore=chore_at_index_4).roommate, self.alice
        )
