Rest time rules apply only to working schedules with **Flexible Hours** enabled.
Non-flexible schedules are not affected.

Set up rest time rules on the working schedule:

1. Go to **Employees ‣ Configuration ‣ Working Schedules**.
2. Open the schedule used by the employees.
3. In the **Rest Time Rules** table, add one or more rules:
   - **Minimum Hours**: gross worked hours (check-out minus check-in) must be
     greater than or equal to this value for the rule to apply.
   - **Rest Time**: hours to deduct when the rule applies.

Rules are evaluated from the highest **Minimum Hours** value downward.
The first matching rule is applied; if no rule matches, no rest time is deducted.

**Example configuration:**

| Minimum Hours | Rest Time |
|---------------|-----------|
| 9:00          | 1:30      |
| 6:00          | 1:00      |

With this setup:
- 10h gross → 1.5h deducted → 8.5h worked
- 7h gross → 1.0h deducted → 6.0h worked
- 4h gross → no rule matches → 4.0h worked (no deduction)
