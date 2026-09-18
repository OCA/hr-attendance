This module adds a configurable rule-based engine to compute time credits on
attendance records. Common use cases include travel time, dressing/changing
time, paid breaks, setup time, and **day-type premiums** (weekend surcharges,
non-working-day bonuses) — any attendance-linked credit that collective
agreements treat separately from overtime and leave.

Time credit rules support two computation modes:

- **Fixed**: a constant number of minutes (or a server-action computed value).
- **Worked Time Factor**: a multiplier on the employee's worked hours.
  For example, factor 1.5 on an 8-hour shift adds 4 hours of credit (total
  12 hours). The factor can be applied to raw worked hours or to the
  accumulated total including prior credits from higher-priority rules.

Rules use Odoo domains or server actions evaluated against attendance fields to
determine when they apply. The built-in `check_in_day_type` field classifies
each attendance as **Working Day** or **Non-Working Day** based on the
employee's resource calendar — no custom code needed for the most common
weekend/rest-day conditions.

When an attendance spans midnight, factor rules evaluate each calendar-day
portion independently so that different day-type premiums apply correctly to
each segment (e.g., the Friday portion at a standard rate and the Saturday
portion at a weekend premium rate).

Each rule supports a rate multiplier and an optional minutes cap, so patterns
like half-rate credits or per-day caps need no custom code. Manual credits can
also be added directly on attendance records.

Credits are computed **reactively**: they are created or replaced automatically
whenever an attendance record is saved or its key fields are updated. Changes to
rules cascade immediately to all unlocked attendances in the affected company.
Records can be locked once a pay period is closed to prevent any further
automatic or manual changes to their credit lines.

## Reporting

The **Monthly Time Credit Summary** report (Attendances › Reporting) aggregates
worked and credited hours per employee per month in pivot, graph, and list views.
Managers can compare worked hours against credited hours, drill into any period,
and group by employee or month.

A **Print Monthly Report** wizard generates a QWeb PDF for any date range and
optional employee selection. The report includes one section per employee with
full attendance detail (credited hours broken down by type) and a grand
summary table.

Employees can view their own monthly summary at Attendances › My Time Credits
(read-only, automatically scoped to their own records).
