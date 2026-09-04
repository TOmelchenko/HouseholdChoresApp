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
- Chores rotate automatically between roommates using equal turns (round-robin).

## 4. Completing Chores

- A roommate marks a chore complete with one tap.
- Completion happens immediately.
- No confirmation is required.
- Each chore displays:
  - Due date
  - Due/overdue status

## 5. Overdue Chores

- An overdue chore remains assigned to the same roommate.
- There is no additional penalty.
- The chore remains outstanding until completed.

## 6. Main Screen

Keep the interface minimal.

The main screen shows:

- The current user's chores
- Their due dates
- Their due/overdue status

Do not include a large household dashboard in the MVP.

## 7. Notifications

No reminders for the MVP.

Specifically:

- No push reminders
- No daily reminders
- No overdue notifications

## 8. Explicitly Out of Scope

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
- Effort scores or effort-based fairness
- Chore swapping
- Vacation mode

## 9. Core Product Principle

> Give every roommate a fair share of the household work, without making them manage the system.

## 10. MVP User Flow

1. First roommate opens the app.
2. A household is created automatically.
3. The household receives a permanent shared code.
4. Other roommates enter the code to join.
5. The household uses predefined chores with fixed frequencies.
6. The system automatically assigns chores using round-robin rotation.
7. Roommates see only their own chores.
8. A roommate completes a chore with one tap.
9. Missed chores remain assigned and carry over.

## 11. MVP Success Criteria

The MVP should make it possible for a household to:

- Set up a shared household without accounts.
- Add 2–6 roommates.
- Use predefined recurring chores.
- Automatically distribute chores fairly using round-robin rotation.
- Clearly see what each roommate needs to do.
- Complete chores with minimal interaction.
- Handle missed chores without manual re-planning.
