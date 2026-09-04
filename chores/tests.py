import datetime

from django.test import TestCase
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
