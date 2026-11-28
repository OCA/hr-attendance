Go to Attendances > Configuration > Time Credit Types to create the categories
of credits your organization uses (e.g. `travel`, `dressing`, `sunday_premium`,
`holiday_surcharge`). Each type has a free-text **Code** that must be unique per
company. There are no predefined codes — name them to match your collective
agreement or payroll system.

Then go to Attendances > Configuration > Time Credit Rules to define the rules
that automatically assign credits. Each rule specifies:

- **Credit Type**: the type of credit produced when this rule fires.
- **Condition**: a domain filter on the attendance record, or a server action
  of type *Execute Code* that sets `action = True` when the rule should trigger.
- **Computation Mode** (`minutes_type`):
  - *Fixed*: a constant number of minutes per attendance.
  - *Server Action*: a code block that sets `action = <integer>` with the
    computed minutes.
  - *Worked Time Factor*: credits extra time as a multiple of worked hours.
    Set **Factor Value** (e.g. `1.5` = 50% premium) and **Factor Base**
    (`Worked Hours Only` or `Worked Hours + Prior Credits`).
- **Rate**: a multiplier applied to the computed minutes before rounding
  (default 1.0). Use `0.5` to grant half the base time, `1.5` for
  time-and-a-half.
- **Minutes Cap**: an upper bound on the minutes this rule can grant per
  attendance (0 = no cap). Applied after the rate multiplier.

Rules are evaluated in **sequence order** and all matching rules produce a
credit line — the engine does not stop at the first match. A rule without
company applies to every company. Saving or deleting a rule immediately
reprocesses the unlocked, checked-out attendances of the rule's company inside
the lookback window (see *Scheduled action* below); the **Process Time Credits**
action refreshes a wider selection.

**Day-type conditions**

The `check_in_day_type` field on `hr.attendance` classifies each attendance as
`working_day` or `non_working_day` based on the employee's resource calendar.
Two-week calendars use the week type of the date, and calendar lines limited by
`date_from`/`date_to` only count inside their range. Use it directly in domain
conditions:

- `[('check_in_day_type', '=', 'non_working_day')]` — matches Saturdays,
  Sundays, and any other day not in the employee's calendar.
- `[('check_in_day_type', '=', 'working_day')]` — matches standard working days.

For midnight-crossing attendances, factor rules evaluate each calendar-day
segment independently, so a rule targeting `non_working_day` will produce a
separate credit line for the Saturday portion of a Friday–Saturday session.

**Public-holiday condition**

`is_public_holiday` on `hr.attendance` is true when the check-in day is covered
by a global leave on the employee's calendar. The flag and the rules that depend
on it are refreshed when a global leave is created, changed or removed, so a
holiday entered after the attendance still grants its credit.

**Locking**

Once credit lines for a pay period have been reported or transferred externally,
set **Credit Locked** on the relevant attendance records to prevent any further
changes. Locking can be applied per-record from the form view or in batch via
any standard Odoo list action.

**Scheduled action**

The module installs a daily scheduled action (*Attendance: Process Time Credit
Rules*) as a safety net. Under normal operation this cron is not needed —
credits are kept current by the reactive write/create triggers — but it guards
against records created via raw SQL or external integrations that bypass the
ORM. It sweeps the last 90 days by default; set the system parameter
`hr_attendance_time_credit.cron_lookback_days` to another number of days, or to
`0` for no cutoff. The same window bounds the rule-change cascade. Locked
records are excluded from the sweep. Adjust the interval or disable the cron
from Settings > Technical > Scheduled Actions.
