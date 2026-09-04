"""Unit tests for chores/rotation.py.

These are plain unittest.TestCase (not Django TestCase) since next_assignee
is a pure function with no database dependency. They still run under
`python manage.py test` per Django's test discovery.
"""

import unittest

from .rotation import next_assignee


class NextAssigneeTest(unittest.TestCase):
    def test_single_roommate_first_assignment(self):
        self.assertEqual(next_assignee([5], []), 5)

    def test_single_roommate_stays_assigned_regardless_of_history_length(self):
        self.assertEqual(next_assignee([5], [5, 5, 5]), 5)

    def test_multiple_roommates_first_assignment_picks_first(self):
        self.assertEqual(next_assignee([1, 2, 3], []), 1)

    def test_normal_round_robin_step(self):
        self.assertEqual(next_assignee([1, 2, 3], [1]), 2)

    def test_full_cycle_wraps_back_to_start(self):
        self.assertEqual(next_assignee([1, 2, 3], [1, 2, 3]), 1)

    def test_multiple_full_cycles_only_looks_at_most_recent_entry(self):
        self.assertEqual(next_assignee([1, 2, 3], [1, 2, 3, 1, 2, 3, 1]), 2)

    def test_falls_back_to_most_recent_entry_still_in_roommate_ids(self):
        # history's most recent entry (9) is not in roommate_ids (roommate
        # left the household); the function falls back to the most recent
        # entry that IS still a current roommate (2) and returns the one
        # after it in roommate_ids order, which is 3.
        #
        # NOTE: issue #7's acceptance criteria states this case should
        # return 1, but that contradicts its own stated reasoning ("falls
        # back to entry 2 and returns the one after it" -> 3, not 1). Flagged
        # on the issue; this test encodes the algorithm consistent with the
        # documented reasoning and with all other examples in the issue.
        self.assertEqual(next_assignee([1, 2, 3], [1, 2, 9]), 3)

    def test_all_history_entries_no_longer_roommates_treated_as_first_assignment(self):
        self.assertEqual(next_assignee([1, 2, 3], [9, 8]), 1)

    def test_empty_roommate_ids_raises_value_error(self):
        with self.assertRaises(ValueError):
            next_assignee([], [])

    def test_empty_roommate_ids_with_nonempty_history_raises_value_error(self):
        with self.assertRaises(ValueError):
            next_assignee([], [1, 2])

    def test_newly_joined_roommate_picked_up_on_their_turn(self):
        self.assertEqual(next_assignee([1, 2, 3, 4], [1, 2, 3]), 4)


if __name__ == "__main__":
    unittest.main()
