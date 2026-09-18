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
credit line — the engine does not stop at the first match. Saving or deleting a
rule immediately reprocesses all unlocked, checked-out attendances in the
rule's company.

**Day-type conditions**

The `check_in_day_type` field on `hr.attendance` classifies each attendance as
`working_day` or `non_working_day` based on the employee's resource calendar.
Use it directly in domain conditions:

- `[('check_in_day_type', '=', 'non_working_day')]` — matches Saturdays,
  Sundays, and any other day not in the employee's calendar.
- `[('check_in_day_type', '=', 'working_day')]` — matches standard working days.

For midnight-crossing attendances, factor rules evaluate each calendar-day
segment independently, so a rule targeting `non_working_day` will produce a
separate credit line for the Saturday portion of a Friday–Saturday session.

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
ORM. Locked records are excluded from the sweep. Adjust the interval or disable
the cron from Settings > Technical > Scheduled Actions.
