This module deducts a configurable rest time from attendance worked hours for employees
on **flexible working schedules**.

Flexible-schedule employees do not have fixed time slots in their calendar, so standard
lunch or break deductions are not applied automatically. This can overstate effective
worked hours and overtime.

The module adds **Rest Time Rules** on working schedules (`resource.calendar`). Each
rule specifies a minimum gross worked hours threshold and the rest time to deduct when
that threshold is met. Rules are evaluated from the highest threshold downward; the
first matching rule is applied. Rules are only evaluated for employees whose working
schedule has **Flexible Hours** enabled; non-flexible schedules are not affected.

New attendance records automatically apply the matching rule based on the gross time
between check-in and check-out. The value can also be adjusted manually on each
attendance record when needed.
