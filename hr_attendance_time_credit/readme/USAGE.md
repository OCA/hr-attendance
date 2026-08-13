Time credits are computed **automatically** whenever an attendance record is
created or its check-in, check-out, employee, or skip-time-credit fields are
written. The rule engine evaluates each active rule in sequence order and
creates one credit line per matching rule (or one line per matching calendar-day
segment for midnight-crossing factor rules).

Each rule computes a minutes value, applies the **rate** multiplier, and then
clamps the result to the **minutes cap** (if set). The **Total Credited Hours**
field reflects the original worked hours plus all credit minutes converted to
hours. Time credits are supplementary; the field combines both for reporting
convenience.

The **Day Type** field on the attendance record indicates whether the check-in
day is a **Working Day** or **Non-Working Day** based on the employee's resource
calendar. It can be used in domain conditions without server-action code.

**Computation modes**

- **Fixed**: a constant number of minutes per attendance.
- **Server Action**: a server-action code block that sets `action = <integer>`
  with the computed minutes. Available context: `record`, `env`, `datetime`,
  `dateutil`, `time`, `timezone`.
- **Worked Time Factor**: credits additional time as a multiple of worked hours.
  `credit_minutes = base_hours × 60 × (factor − 1.0)`. Use **Factor Base**
  to control whether the base is raw worked hours or worked hours plus credits
  from earlier rules (lower sequence number).

**Midnight-crossing attendances**

When a factor rule is evaluated against an attendance that spans multiple
calendar days, the engine splits the attendance into per-calendar-day segments
and evaluates the rule's domain independently for each segment. This allows
different day-type factors to apply to different portions of the same session.
Each credit line produced by this path carries a **Segment Date** and
**Segment Hours** for traceability.

**Editing attendance records**

Any change to check-in, check-out, employee, or skip-time-credit replaces the
automatic credit lines immediately: old automatic lines are removed and new ones
are created based on the current rules. Manual lines (`origin = Manual`) are
never touched by the engine and survive every recompute.

**Editing or deleting rules**

Saving or deleting a rule triggers a recompute of all unlocked, checked-out
attendances in the rule's company.

**Locking records**

Attendance managers can set **Credit Locked** on an attendance record to freeze
its credit lines. A locked record is skipped by all automatic recomputation:
reactive writes, rule-change cascades, cron sweeps, and the force reprocess
action. Unlock the record before making any corrections.

Locking is intended to protect records that have already been reported or
transferred to payroll.

**Force reprocess**

Attendance managers can select one or more attendance records in the list view
and use the **Process Time Credits** server action to force a full recompute.
Useful after bulk imports performed with the `skip_time_credit_recompute`
context flag, or to recover from unexpected inconsistency. Locked records are
ignored even by this action.

**Bulk imports**

When importing or creating attendance records in bulk, pass the context key
`skip_time_credit_recompute=True` to suppress per-record processing during the
import. After the import completes, use the **Process Time Credits** action or
run the safety-net cron to process all records at once.

**Skip Time Credit**

Attendance managers can set the **Skip Time Credit** flag on individual records
to exclude them from all automatic processing. Setting this flag also removes
any existing automatic lines from the record immediately.

**Reporting**

Go to Attendances > Reporting > Time Credits for a dedicated view of all credit
lines across employees. The list can be filtered by type, employee, origin, or
date range and grouped by type, employee, origin, month, or segment date. The
pivot view shows credited minutes by employee, type, and month.

The base attendance list view includes **Credited Hours** as an optional column
(hidden by default). The search view includes filters for **Non-Working Day**,
**Working Day**, **Has Time Credits**, **Locked**, and **Skipped**, plus
**Day Type** and other group-by options.

## Monthly Reporting

**Monthly Time Credit Summary (managers)**

Go to Attendances › Reporting › Monthly Time Credit Summary. The pivot view
shows worked hours, credited hours, and total hours per employee per month.
Switch to graph view for a bar chart. Use the list view for a flat exportable
table. Quick filters "This Month" and "Last Month" are available in the search bar.

**Print Monthly Report**

Go to Attendances › Reporting › Print Monthly Report. Select a date range and
optionally filter by specific employees. Click Print Report to generate a PDF
showing per-employee attendance detail rows (with credited hours by type),
employee subtotals, and a grand summary table.

**My Time Credits (employees)**

Employees access Attendances › My Time Credits to view their own monthly
summary. The view is read-only and scoped automatically to the current user.
