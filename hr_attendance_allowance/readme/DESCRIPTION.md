This module adds a configurable rule-based engine to compute time allowances
(complementary time credits) on attendance records. Common use cases include
travel time, dressing/changing time, paid breaks, and setup time — any
attendance-linked credit that collective agreements treat separately from
overtime and leave. Allowance rules use Odoo domains or server actions
evaluated against attendance fields to determine when and how much extra time
should be credited. Each rule supports a rate multiplier and an optional
minutes cap, so patterns like half-rate credits or per-day caps need no custom
code. Manual allowances can also be added directly on
attendance records.

Allowances are computed **reactively**: they are created or replaced
automatically whenever an attendance record is saved or its check-in,
check-out, or skip-allowance fields are updated. Changes to allowance rules
cascade immediately to all unlocked attendances in the affected company.
Records can be locked once a pay period is closed to prevent any further
automatic or manual changes to their allowance lines.
