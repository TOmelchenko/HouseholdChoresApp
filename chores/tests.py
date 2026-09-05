import datetime
import threading
from unittest import mock

from django.db import IntegrityError, transaction
from django.test import Client, TestCase, TransactionTestCase
from django.utils import timezone

from .models import Assignment, Chore, Household, Roommate


class SmokeTest(TestCase):
    def test_true(self):
        self.assertTrue(True)


class IndexViewTest(TestCase):
    def test_empty_session_shows_landing_page(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Create household")
        self.assertContains(response, "Join household")

    def test_valid_session_redirects_to_my_chores(self):
        household = Household.objects.create()
        roommate = Roommate.objects.create(household=household, name="Alice")
        session = self.client.session
        session["household_id"] = household.id
        session["roommate_id"] = roommate.id
        session.save()

        response = self.client.get("/")

        self.assertRedirects(response, "/chores/")

    def test_stale_household_id_clears_session_and_shows_landing_page(self):
        session = self.client.session
        session["household_id"] = 9999
        session["roommate_id"] = 9999
        session.save()

        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Create household")
        session = self.client.session
        self.assertNotIn("household_id", session)
        self.assertNotIn("roommate_id", session)

    def test_partial_session_missing_roommate_id_shows_landing_page(self):
        household = Household.objects.create()
        session = self.client.session
        session["household_id"] = household.id
        session.save()

        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Create household")
        session = self.client.session
        self.assertNotIn("household_id", session)
        self.assertNotIn("roommate_id", session)


class MyChoresViewTest(TestCase):
    def setUp(self):
        self.household = Household.objects.create()
        self.roommate = Roommate.objects.create(household=self.household, name="Alice")
        self.chore = Chore.objects.create(name="Dishes", frequency_days=1)

    def _login(self, household=None, roommate=None):
        household = household or self.household
        roommate = roommate or self.roommate
        session = self.client.session
        session["household_id"] = household.id
        session["roommate_id"] = roommate.id
        session.save()

    def test_no_session_redirects_to_index(self):
        response = self.client.get("/chores/")
        self.assertRedirects(response, "/")

    def test_invalid_household_id_redirects_and_clears_session(self):
        session = self.client.session
        session["household_id"] = 9999
        session["roommate_id"] = self.roommate.id
        session.save()

        response = self.client.get("/chores/")

        self.assertRedirects(response, "/")
        session = self.client.session
        self.assertNotIn("household_id", session)
        self.assertNotIn("roommate_id", session)

    def test_invalid_roommate_id_redirects_and_clears_session(self):
        session = self.client.session
        session["household_id"] = self.household.id
        session["roommate_id"] = 9999
        session.save()

        response = self.client.get("/chores/")

        self.assertRedirects(response, "/")
        session = self.client.session
        self.assertNotIn("household_id", session)
        self.assertNotIn("roommate_id", session)

    def test_roommate_household_mismatch_redirects_and_clears_session(self):
        other_household = Household.objects.create()
        other_roommate = Roommate.objects.create(household=other_household, name="Bob")
        session = self.client.session
        session["household_id"] = self.household.id
        session["roommate_id"] = other_roommate.id
        session.save()

        response = self.client.get("/chores/")

        self.assertRedirects(response, "/")
        session = self.client.session
        self.assertNotIn("household_id", session)
        self.assertNotIn("roommate_id", session)

    def test_shows_logged_in_roommate_name(self):
        self._login()

        response = self.client.get("/chores/")

        self.assertContains(response, "Logged in as")
        self.assertContains(response, "Alice")

    def test_zero_incomplete_assignments_shows_empty_state(self):
        self._login()

        response = self.client.get("/chores/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No chores right now")

    def test_valid_session_lists_incomplete_assignments_sorted_by_due_date(self):
        today = timezone.localdate()
        chore2 = Chore.objects.create(name="Laundry", frequency_days=7)
        Assignment.objects.create(
            chore=chore2, roommate=self.roommate, due_date=today + datetime.timedelta(days=5)
        )
        Assignment.objects.create(
            chore=self.chore, roommate=self.roommate, due_date=today - datetime.timedelta(days=1)
        )
        self._login()

        response = self.client.get("/chores/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Dishes")
        self.assertContains(response, "Laundry")
        dishes_pos = response.content.decode().find("Dishes")
        laundry_pos = response.content.decode().find("Laundry")
        self.assertLess(dishes_pos, laundry_pos)

    def test_overdue_assignment_is_flagged(self):
        today = timezone.localdate()
        Assignment.objects.create(
            chore=self.chore, roommate=self.roommate, due_date=today - datetime.timedelta(days=1)
        )
        self._login()

        response = self.client.get("/chores/")

        self.assertContains(response, "Overdue")

    def test_due_today_assignment_is_not_flagged_overdue(self):
        today = timezone.localdate()
        Assignment.objects.create(chore=self.chore, roommate=self.roommate, due_date=today)
        self._login()

        response = self.client.get("/chores/")

        self.assertNotContains(response, "Overdue")

    def test_completed_assignment_excluded(self):
        today = timezone.localdate()
        Assignment.objects.create(
            chore=self.chore,
            roommate=self.roommate,
            due_date=today,
            completed_at=timezone.now(),
        )
        self._login()

        response = self.client.get("/chores/")

        self.assertContains(response, "No chores right now")

    def test_other_roommate_assignment_excluded(self):
        other_roommate = Roommate.objects.create(household=self.household, name="Bob")
        today = timezone.localdate()
        Assignment.objects.create(chore=self.chore, roommate=other_roommate, due_date=today)
        self._login()

        response = self.client.get("/chores/")

        self.assertContains(response, "No chores right now")

    def test_other_household_assignment_excluded(self):
        other_household = Household.objects.create()
        other_roommate = Roommate.objects.create(household=other_household, name="Carol")
        today = timezone.localdate()
        Assignment.objects.create(chore=self.chore, roommate=other_roommate, due_date=today)
        self._login()

        response = self.client.get("/chores/")

        self.assertContains(response, "No chores right now")


class CompleteChoreViewTest(TestCase):
    def setUp(self):
        self.household = Household.objects.create()
        self.roommate = Roommate.objects.create(household=self.household, name="Alice")
        self.chore = Chore.objects.create(name="Dishes", frequency_days=1)
        self.assignment = Assignment.objects.create(
            chore=self.chore, roommate=self.roommate, due_date=timezone.localdate()
        )

    def _login(self, household=None, roommate=None):
        household = household or self.household
        roommate = roommate or self.roommate
        session = self.client.session
        session["household_id"] = household.id
        session["roommate_id"] = roommate.id
        session.save()

    def test_post_completes_assignment_and_redirects(self):
        self._login()

        response = self.client.post(f"/chores/{self.assignment.id}/complete/")

        self.assertRedirects(response, "/chores/")
        self.assignment.refresh_from_db()
        self.assertIsNotNone(self.assignment.completed_at)

    def test_completed_assignment_no_longer_in_my_chores(self):
        self._login()

        self.client.post(f"/chores/{self.assignment.id}/complete/")
        response = self.client.get("/chores/")

        self.assertContains(response, "No chores right now")

    def test_get_request_returns_405_and_does_not_complete(self):
        self._login()

        response = self.client.get(f"/chores/{self.assignment.id}/complete/")

        self.assertEqual(response.status_code, 405)
        self.assignment.refresh_from_db()
        self.assertIsNone(self.assignment.completed_at)

    def test_nonexistent_assignment_returns_404(self):
        self._login()

        response = self.client.post("/chores/9999/complete/")

        self.assertEqual(response.status_code, 404)

    def test_other_roommates_assignment_returns_404_and_unchanged(self):
        other_roommate = Roommate.objects.create(household=self.household, name="Bob")
        other_assignment = Assignment.objects.create(
            chore=self.chore, roommate=other_roommate, due_date=timezone.localdate()
        )
        self._login()

        response = self.client.post(f"/chores/{other_assignment.id}/complete/")

        self.assertEqual(response.status_code, 404)
        other_assignment.refresh_from_db()
        self.assertIsNone(other_assignment.completed_at)

    def test_other_households_assignment_returns_404_and_unchanged(self):
        other_household = Household.objects.create()
        other_roommate = Roommate.objects.create(household=other_household, name="Carol")
        other_assignment = Assignment.objects.create(
            chore=self.chore, roommate=other_roommate, due_date=timezone.localdate()
        )
        self._login()

        response = self.client.post(f"/chores/{other_assignment.id}/complete/")

        self.assertEqual(response.status_code, 404)
        other_assignment.refresh_from_db()
        self.assertIsNone(other_assignment.completed_at)

    def test_double_post_is_idempotent_and_keeps_original_timestamp(self):
        self._login()

        first_response = self.client.post(f"/chores/{self.assignment.id}/complete/")
        self.assignment.refresh_from_db()
        first_completed_at = self.assignment.completed_at

        second_response = self.client.post(f"/chores/{self.assignment.id}/complete/")
        self.assignment.refresh_from_db()

        self.assertRedirects(second_response, "/chores/")
        self.assertEqual(self.assignment.completed_at, first_completed_at)

    def test_no_session_redirects_to_index(self):
        response = self.client.post(f"/chores/{self.assignment.id}/complete/")

        self.assertRedirects(response, "/")
        self.assignment.refresh_from_db()
        self.assertIsNone(self.assignment.completed_at)

    def test_stale_session_redirects_to_index_and_clears_session(self):
        session = self.client.session
        session["household_id"] = 9999
        session["roommate_id"] = 9999
        session.save()

        response = self.client.post(f"/chores/{self.assignment.id}/complete/")

        self.assertRedirects(response, "/")
        session = self.client.session
        self.assertNotIn("household_id", session)
        self.assertNotIn("roommate_id", session)

    def test_missing_csrf_token_returns_403(self):
        self._login()
        csrf_client = self.client_class(enforce_csrf_checks=True)
        session = csrf_client.session
        session["household_id"] = self.household.id
        session["roommate_id"] = self.roommate.id
        session.save()

        response = csrf_client.post(f"/chores/{self.assignment.id}/complete/")

        self.assertEqual(response.status_code, 403)


class MyChoresRecentlyCompletedTest(TestCase):
    def setUp(self):
        self.household = Household.objects.create()
        self.roommate = Roommate.objects.create(household=self.household, name="Alice")
        self.chore = Chore.objects.create(name="Dishes", frequency_days=1)

    def _login(self, household=None, roommate=None):
        household = household or self.household
        roommate = roommate or self.roommate
        session = self.client.session
        session["household_id"] = household.id
        session["roommate_id"] = roommate.id
        session.save()

    def test_recently_completed_section_absent_when_nothing_to_show(self):
        self._login()

        response = self.client.get("/chores/")

        self.assertNotContains(response, "Recently completed")

    def test_recently_completed_section_shown_within_window(self):
        Assignment.objects.create(
            chore=self.chore,
            roommate=self.roommate,
            due_date=timezone.localdate(),
            completed_at=timezone.now(),
        )
        self._login()

        response = self.client.get("/chores/")

        self.assertContains(response, "Recently completed")
        self.assertContains(response, "Dishes")
        self.assertContains(response, "Undo")

    def test_recently_completed_excludes_completions_older_than_5_minutes(self):
        Assignment.objects.create(
            chore=self.chore,
            roommate=self.roommate,
            due_date=timezone.localdate(),
            completed_at=timezone.now() - datetime.timedelta(minutes=6),
        )
        self._login()

        response = self.client.get("/chores/")

        self.assertNotContains(response, "Recently completed")

    def test_recently_completed_ordered_most_recent_first(self):
        older = Assignment.objects.create(
            chore=self.chore,
            roommate=self.roommate,
            due_date=timezone.localdate(),
            completed_at=timezone.now() - datetime.timedelta(minutes=2),
        )
        chore2 = Chore.objects.create(name="Laundry", frequency_days=7)
        newer = Assignment.objects.create(
            chore=chore2,
            roommate=self.roommate,
            due_date=timezone.localdate(),
            completed_at=timezone.now() - datetime.timedelta(minutes=1),
        )
        self._login()

        response = self.client.get("/chores/")

        content = response.content.decode()
        laundry_pos = content.find("Laundry")
        dishes_pos = content.find("Dishes")
        self.assertLess(laundry_pos, dishes_pos)


class UndoChoreViewTest(TestCase):
    def setUp(self):
        self.household = Household.objects.create()
        self.roommate = Roommate.objects.create(household=self.household, name="Alice")
        self.chore = Chore.objects.create(name="Dishes", frequency_days=1)
        self.assignment = Assignment.objects.create(
            chore=self.chore,
            roommate=self.roommate,
            due_date=timezone.localdate(),
            completed_at=timezone.now(),
        )

    def _login(self, household=None, roommate=None):
        household = household or self.household
        roommate = roommate or self.roommate
        session = self.client.session
        session["household_id"] = household.id
        session["roommate_id"] = roommate.id
        session.save()

    def test_undo_within_window_clears_completed_at_and_redirects(self):
        self._login()

        response = self.client.post(f"/chores/{self.assignment.id}/undo/")

        self.assertRedirects(response, "/chores/")
        self.assignment.refresh_from_db()
        self.assertIsNone(self.assignment.completed_at)

    def test_undo_moves_assignment_back_to_pending_list(self):
        self._login()

        self.client.post(f"/chores/{self.assignment.id}/undo/")
        response = self.client.get("/chores/")

        self.assertContains(response, "Dishes")
        self.assertNotContains(response, "Recently completed")

    def test_undo_after_5_minute_window_is_noop(self):
        self.assignment.completed_at = timezone.now() - datetime.timedelta(minutes=5, seconds=1)
        self.assignment.save(update_fields=["completed_at"])
        self._login()
        original_completed_at = self.assignment.completed_at

        response = self.client.post(f"/chores/{self.assignment.id}/undo/")

        self.assertRedirects(response, "/chores/")
        self.assignment.refresh_from_db()
        self.assertEqual(self.assignment.completed_at, original_completed_at)

    def test_undo_other_roommates_assignment_returns_404_and_unchanged(self):
        other_roommate = Roommate.objects.create(household=self.household, name="Bob")
        other_assignment = Assignment.objects.create(
            chore=self.chore,
            roommate=other_roommate,
            due_date=timezone.localdate(),
            completed_at=timezone.now(),
        )
        self._login()

        response = self.client.post(f"/chores/{other_assignment.id}/undo/")

        self.assertEqual(response.status_code, 404)
        other_assignment.refresh_from_db()
        self.assertIsNotNone(other_assignment.completed_at)

    def test_undo_other_households_assignment_returns_404_and_unchanged(self):
        other_household = Household.objects.create()
        other_roommate = Roommate.objects.create(household=other_household, name="Carol")
        other_assignment = Assignment.objects.create(
            chore=self.chore,
            roommate=other_roommate,
            due_date=timezone.localdate(),
            completed_at=timezone.now(),
        )
        self._login()

        response = self.client.post(f"/chores/{other_assignment.id}/undo/")

        self.assertEqual(response.status_code, 404)
        other_assignment.refresh_from_db()
        self.assertIsNotNone(other_assignment.completed_at)

    def test_undo_nonexistent_assignment_returns_404(self):
        self._login()

        response = self.client.post("/chores/9999/undo/")

        self.assertEqual(response.status_code, 404)

    def test_get_request_returns_405_and_does_not_change_completed_at(self):
        self._login()

        response = self.client.get(f"/chores/{self.assignment.id}/undo/")

        self.assertEqual(response.status_code, 405)
        self.assignment.refresh_from_db()
        self.assertIsNotNone(self.assignment.completed_at)

    def test_double_post_undo_is_idempotent(self):
        self._login()

        first_response = self.client.post(f"/chores/{self.assignment.id}/undo/")
        self.assignment.refresh_from_db()
        self.assertIsNone(self.assignment.completed_at)

        second_response = self.client.post(f"/chores/{self.assignment.id}/undo/")

        self.assertRedirects(second_response, "/chores/")
        self.assignment.refresh_from_db()
        self.assertIsNone(self.assignment.completed_at)

    def test_no_session_redirects_to_index(self):
        response = self.client.post(f"/chores/{self.assignment.id}/undo/")

        self.assertRedirects(response, "/")
        self.assignment.refresh_from_db()
        self.assertIsNotNone(self.assignment.completed_at)

    def test_stale_session_redirects_to_index_and_clears_session(self):
        session = self.client.session
        session["household_id"] = 9999
        session["roommate_id"] = 9999
        session.save()

        response = self.client.post(f"/chores/{self.assignment.id}/undo/")

        self.assertRedirects(response, "/")
        session = self.client.session
        self.assertNotIn("household_id", session)
        self.assertNotIn("roommate_id", session)

    def test_missing_csrf_token_returns_403(self):
        self._login()
        csrf_client = self.client_class(enforce_csrf_checks=True)
        session = csrf_client.session
        session["household_id"] = self.household.id
        session["roommate_id"] = self.roommate.id
        session.save()

        response = csrf_client.post(f"/chores/{self.assignment.id}/undo/")

        self.assertEqual(response.status_code, 403)


class CreateHouseholdViewTest(TestCase):
    def test_get_renders_form(self):
        response = self.client.get("/create/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "<form")

    def test_post_creates_household_and_roommate(self):
        response = self.client.post("/create/", {"name": "Alice"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Household.objects.count(), 1)
        self.assertEqual(Roommate.objects.count(), 1)
        self.assertContains(response, "Alice")

    def test_post_persists_ids_to_session(self):
        self.client.post("/create/", {"name": "Alice"})
        session = self.client.session
        self.assertIn("household_id", session)
        self.assertIn("roommate_id", session)

    def test_post_displays_household_code(self):
        self.client.post("/create/", {"name": "Alice"})
        household = Household.objects.first()
        response = self.client.post("/create/", {"name": "Bob"})
        self.assertContains(response, Household.objects.last().code)

    def test_post_shows_link_to_my_chores(self):
        response = self.client.post("/create/", {"name": "Alice"})
        self.assertContains(response, 'href="/chores/"')


class JoinHouseholdViewTest(TestCase):
    def setUp(self):
        self.household = Household.objects.create()

    def test_get_renders_form(self):
        response = self.client.get("/join/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "<form")

    def test_post_with_valid_code_creates_roommate(self):
        response = self.client.post("/join/", {"code": self.household.code, "name": "Bob"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Roommate.objects.count(), 1)
        self.assertContains(response, "Bob")

    def test_post_with_valid_code_persists_ids_to_session(self):
        self.client.post("/join/", {"code": self.household.code, "name": "Bob"})
        session = self.client.session
        self.assertEqual(session["household_id"], self.household.id)
        self.assertIn("roommate_id", session)

    def test_post_with_invalid_code_shows_error(self):
        response = self.client.post("/join/", {"code": "BADCODE1", "name": "Bob"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No household found")
        self.assertEqual(Roommate.objects.count(), 0)

    def test_post_with_invalid_code_does_not_set_session(self):
        self.client.post("/join/", {"code": "BADCODE1", "name": "Bob"})
        session = self.client.session
        self.assertNotIn("household_id", session)

    def test_post_code_lookup_is_case_insensitive(self):
        response = self.client.post("/join/", {"code": self.household.code.lower(), "name": "Bob"})
        self.assertEqual(Roommate.objects.count(), 1)

    def test_post_shows_link_to_my_chores(self):
        response = self.client.post("/join/", {"code": self.household.code, "name": "Bob"})
        self.assertContains(response, 'href="/chores/"')

    def test_post_with_matching_name_resumes_existing_roommate(self):
        existing = Roommate.objects.create(household=self.household, name="Bob")

        response = self.client.post("/join/", {"code": self.household.code, "name": "Bob"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Roommate.objects.count(), 1)
        self.assertContains(response, "Welcome back, Bob!")
        session = self.client.session
        self.assertEqual(session["roommate_id"], existing.id)

    def test_post_with_matching_name_case_insensitive_resumes_existing_roommate(self):
        existing = Roommate.objects.create(household=self.household, name="Bob")

        response = self.client.post("/join/", {"code": self.household.code, "name": "BOB"})

        self.assertEqual(Roommate.objects.count(), 1)
        session = self.client.session
        self.assertEqual(session["roommate_id"], existing.id)
        self.assertContains(response, "Welcome back, Bob!")

    def test_post_with_matching_name_whitespace_resumes_existing_roommate(self):
        existing = Roommate.objects.create(household=self.household, name="Bob")

        response = self.client.post("/join/", {"code": self.household.code, "name": " Bob "})

        self.assertEqual(Roommate.objects.count(), 1)
        session = self.client.session
        self.assertEqual(session["roommate_id"], existing.id)
        self.assertContains(response, "Welcome back, Bob!")

    def test_post_with_non_matching_name_creates_new_roommate(self):
        Roommate.objects.create(household=self.household, name="Bob")

        response = self.client.post("/join/", {"code": self.household.code, "name": "Carol"})

        self.assertEqual(Roommate.objects.count(), 2)
        new_roommate = Roommate.objects.get(name="Carol")
        session = self.client.session
        self.assertEqual(session["roommate_id"], new_roommate.id)
        self.assertContains(response, "Welcome, Carol!")
        self.assertNotContains(response, "Welcome back")

    def test_creating_second_case_insensitive_duplicate_name_violates_db_constraint(self):
        # Superseded by #18: this used to construct two pre-existing "Bob" rows
        # directly via the ORM to exercise join_household's "resume the lowest
        # id among matches" fallback for legacy duplicate data. The DB-level,
        # case-insensitive backstop constraint added in #18 to close the
        # concurrent-join race (see JoinHouseholdRaceTest) makes that scenario
        # permanently impossible to construct -- any second case-insensitive
        # same-name Roommate in the same household now fails at the DB layer,
        # which this test verifies instead.
        Roommate.objects.create(household=self.household, name="Bob")

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Roommate.objects.create(household=self.household, name="bob")

        self.assertEqual(Roommate.objects.count(), 1)


class _FrozenLookup:
    """Stands in for a Roommate queryset whose result was captured earlier, so
    `.order_by(...).first()` replays that frozen answer instead of re-querying
    the (by-then-changed) database."""

    def __init__(self, frozen_first):
        self._frozen_first = frozen_first

    def order_by(self, *args, **kwargs):
        return self

    def first(self):
        return self._frozen_first


class JoinHouseholdRaceTest(TransactionTestCase):
    """Covers #18: two simultaneous joins with the same brand-new name must not
    create two Roommate rows, and the loser must resume rather than crash.

    Uses TransactionTestCase (not TestCase) because plain TestCase wraps each
    test in a transaction that's rolled back at teardown, so fixtures created in
    the test aren't actually committed -- a second thread's own DB connection
    (used below to get request B a real, independent commit) wouldn't be able to
    see them at all.

    Roommate.objects.filter is patched so that the *first* call (request A's
    "does this name already exist?" check) freezes its answer, then -- before
    returning that answer to A -- drives a second, independent request B
    through the *entire* view (its own lookup, its own create, its own commit)
    on a separate thread with the real (unpatched) filter, and joins that
    thread so B is fully finished before A resumes. Because B runs on its own
    connection and is allowed to run to completion first, its commit is real
    and durable -- rolling back A's later, failing transaction can't erase it,
    which is what made an earlier, purely single-connection version of this
    test flaky. Only after B has committed a "Carol" roommate does A see its
    (now-stale) frozen answer of "no existing match" and proceed to attempt its
    own create, deterministically reproducing the exact race in the issue:
    both requests' lookups complete before either request's create commits.
    """

    def test_concurrent_join_same_new_name_creates_only_one_roommate(self):
        household = Household.objects.create()

        original_filter = Roommate.objects.filter
        state = {"triggered": False, "response_b": None}

        def racing_filter(*args, **kwargs):
            if state["triggered"]:
                # Later calls (e.g. request A's post-IntegrityError resume
                # lookup) behave normally -- only the very first call races.
                return original_filter(*args, **kwargs)
            state["triggered"] = True

            # Freeze request A's answer to what it genuinely was at this point:
            # this is a brand-new household with no roommates yet, so "no match"
            # (None), without actually issuing the read on this connection. A
            # real SELECT here would leave connection A holding a SQLite
            # shared-cache read lock on chores_roommate for as long as A's
            # transaction stays open (it does, until A's create() below runs),
            # which would block request B's INSERT on its own connection/thread
            # with a "database table is locked" error unrelated to the actual
            # bug under test.
            frozen_first = None

            # Run request B to completion, on its own thread/connection, and
            # wait for it -- so its lookup, create and commit are all real and
            # already durable by the time A is allowed to proceed.
            def run_b():
                with mock.patch.object(
                    Roommate.objects, "filter", side_effect=original_filter
                ):
                    state["response_b"] = Client().post(
                        "/join/", {"code": household.code, "name": "Carol"}
                    )

            thread = threading.Thread(target=run_b)
            thread.start()
            thread.join(timeout=10)

            return _FrozenLookup(frozen_first)

        with mock.patch.object(Roommate.objects, "filter", side_effect=racing_filter):
            response_a = self.client.post(
                "/join/", {"code": household.code, "name": "Carol"}
            )

        response_b = state["response_b"]
        self.assertIsNotNone(response_b, "request B was never triggered")

        for label, response in (("A", response_a), ("B", response_b)):
            self.assertEqual(response.status_code, 200, msg=f"request {label} failed")
            self.assertNotContains(response, "No household found")

        self.assertEqual(Roommate.objects.filter(household=household).count(), 1)
        roommate = Roommate.objects.get(household=household)
        self.assertEqual(roommate.name, "Carol")
