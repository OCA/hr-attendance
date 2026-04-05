Allowances are computed **automatically** whenever an attendance record is
created or its check-in, check-out, or skip-allowance fields are written.
The rule engine evaluates each active rule in sequence order and creates one
allowance line per matching rule.

Each rule computes a minutes value, applies the **rate** multiplier, and then
clamps the result to the **minutes cap** (if set). The **Total Credited Hours**
field reflects the original worked hours plus all allowance minutes converted
to hours. Allowances are supplementary credits, not worked time; the field
combines both for reporting convenience.

The **Check-in Weekday** field on the attendance record indicates the day of
the week (Monday = 0, Sunday = 6) and can be used in domain conditions to
differentiate weekday from weekend credits without server-action code.

**Editing attendance records**

Any change to check-in, check-out, or skip-allowance replaces the automatic
allowance lines immediately: old automatic lines are removed and new ones are
created based on the current rules. Manual lines (``origin = Manual``) are
never touched by the engine and survive every recompute.

**Editing or deleting allowance rules**

Saving or deleting a rule triggers a recompute of all unlocked, checked-out
attendances in the rule's company.

**Locking records**

Attendance managers can set **Allowance Locked** on an attendance record to
freeze its allowance lines. A locked record is skipped by all automatic
recomputation: reactive writes, rule-change cascades, cron sweeps and the
force reprocess action. Manual lines remain editable only after unlocking.

Locking is intended to protect records that have already been reported or
transferred to payroll. Unlock the record before making any corrections.

**Force reprocess**

Attendance managers can select one or more attendance records in the list view
and use the **Process Allowances** server action to force a full recompute.
This is useful after bulk imports performed with the
``skip_allowance_recompute`` context flag, or to recover from any unexpected
inconsistency. Locked records are ignored even by this action.

**Bulk imports**

When importing or creating attendance records in bulk, pass the context key
``skip_allowance_recompute=True`` to suppress per-record processing during the
import. After the import completes, use the **Process Allowances** action or
run the safety-net cron to process all records at once.

**Skip Allowance**

Attendance managers can set the **Skip Allowance** flag on individual records
to exclude them from all automatic processing. Setting this flag also removes
any existing automatic lines from the record immediately.

**Reporting**

Go to Attendances > Reporting > Allowances for a dedicated view of all
allowance lines across employees. The list can be filtered by type, employee,
origin, or date range and grouped by type, employee, origin, or month. The
pivot view shows credited minutes by employee, type, and month — useful for
period review before payroll transfer.

The base attendance list view includes **Credited Hours** as an optional
column (hidden by default). The graph and pivot views under Attendances >
Reporting > Attendances include **Total Credited Hours** as an additional
measure alongside worked hours.

The attendance search view includes three additional filters: **Has
Allowances**, **Locked**, and **Skipped**, and a **Weekday** group-by option.
