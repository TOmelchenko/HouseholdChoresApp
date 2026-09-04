# Shared Household Chores — MVP Specification

## 1. Target Users

- Roommates
- 2–6 people per household

## 2. Household Setup

- The first person automatically creates the household.
- No user accounts or login.
- Each household has a permanent shared code.
- Other roommates join by entering the household code.
- Joining is intentionally simple for the MVP; no approval workflow.

## 3. Chore System

- Predefined chores only.
- Each chore has its own frequency, such as:
  - Daily
  - Weekly
  - Every 2 weeks
  - Other predefined frequencies as supported
- Chores rotate automatically between roommates.

## 4. Fairness

The rotation should optimize for both:

- Equal turns
- Equal overall effort

The goal is not merely to give everyone the same number of chores, but to balance the total amount of work.

### Effort Scores

Each predefined chore has an effort score.

- The app provides a default effort score.
- Roommates can adjust the score.

Example:

| Chore | Effort |
|---|---:|
| Take out trash | 1 |
| Vacuum | 2 |
| Clean bathroom | 4 |
| Deep clean kitchen | 5 |

The rotation uses effort scores to distribute workload fairly.

## 5. Completing Chores

- A roommate marks a chore complete with one tap.
- Completion happens immediately.
- No confirmation is required.
- Each chore displays:
  - Due date
  - Due/overdue status

## 6. Overdue Chores

- An overdue chore remains assigned to the same roommate.
- There is no additional penalty.
- The chore remains outstanding until completed.
- Missed work carries over and affects that roommate's future workload.

## 7. Chore Swapping

- Roommates can request/swap chores with each other.
- A swap requires approval from both roommates.
- No unilateral swaps.

## 8. Vacation Mode

A roommate can temporarily pause participation.

- Their chores are temporarily redistributed among the remaining roommates.
- When the roommate returns, they resume the rotation from where they left off.

## 9. Main Screen

Keep the interface minimal.

The main screen shows:

- The current user's chores
- Their due dates
- Their due/overdue status

Do not include a large household dashboard in the MVP.

## 10. Notifications

No reminders for the MVP.

Specifically:

- No push reminders
- No daily reminders
- No overdue notifications

## 11. Explicitly Out of Scope

To keep the first version focused, the MVP does not include:

- User accounts or login
- Custom chores
- Push notifications/reminders
- Complex household dashboards
- Gamification
- Points or rewards
- Leaderboards
- Social features
- Approval workflows for joining a household
- Advanced statistics or analytics

## 12. Core Product Principle

> Give every roommate a fair share of the household work, without making them manage the system.

## 13. MVP User Flow

1. First roommate opens the app.
2. A household is created automatically.
3. The household receives a permanent shared code.
4. Other roommates enter the code to join.
5. The household uses predefined chores.
6. Each chore has a frequency and effort score.
7. The system automatically assigns chores using rotation and fairness.
8. Roommates see only their own chores.
9. A roommate completes a chore with one tap.
10. Missed chores remain assigned and carry over.
11. Roommates can swap chores when both approve.
12. A roommate can activate vacation mode; their chores are temporarily redistributed.
13. On return, they resume their previous position in the rotation.

## 14. MVP Success Criteria

The MVP should make it possible for a household to:

- Set up a shared household without accounts.
- Add 2–6 roommates.
- Use predefined recurring chores.
- Automatically distribute chores fairly.
- Balance both number of turns and effort.
- Clearly see what each roommate needs to do.
- Complete chores with minimal interaction.
- Handle missed chores without manual re-planning.
- Temporarily redistribute chores during vacations.
- Swap chores with mutual approval.
