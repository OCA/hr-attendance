This module records employee **breaks** during their attendance, for
labour-compliance reporting (are breaks taken, are they too long?) and to
compute the worked hours net of unpaid breaks.

Breaks are recorded with the usual check out / check in buttons, using the
attendance reasons of `hr_attendance_reason`: checking out with a reason linked
to a break type starts a break, and the next check in ends it. The attendance
of the day is reopened, so a working day stays one attendance that can hold
several breaks (morning coffee, lunch, afternoon coffee).

Each break type is either **paid** or **unpaid**. For every attendance the
module computes:

- **Break Hours**: the total time spent on breaks.
- **Unpaid Break Hours**: the unpaid break time. Time overlapping the lunch
  break of the employee's working schedule is not counted, as Odoo already
  excludes it from the worked hours.
- **Net Worked Hours**: the worked hours minus the unpaid breaks.

The worked hours computed by Odoo are left untouched.
