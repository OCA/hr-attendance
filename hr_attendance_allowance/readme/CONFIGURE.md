Go to Attendances > Configuration > Allowance Types to create the types of
allowances your organization uses (e.g. "Travel Time", "Dressing Time",
"Paid Break").

Then go to Attendances > Configuration > Allowance Rules to define the rules
that automatically assign allowances. Each rule specifies:

- **Condition**: a domain filter on the attendance record, or a server action
  of type *Execute Code* that sets ``action = True`` when the rule should
  trigger.
- **Minutes**: a fixed number of minutes, or a server action of type
  *Execute Code* that sets ``action = <integer>`` with the computed minutes.
- **Rate**: a multiplier applied to the computed minutes before rounding
  (default 1.0). Use 0.5 to grant half the base time, 1.5 for time-and-a-half.
- **Minutes Cap**: an upper bound on the minutes this rule can grant per
  attendance (0 = no cap). Applied after the rate multiplier.

Rules are evaluated in sequence order and **all matching rules produce an
allowance line** — the engine does not stop at the first match. This means a
single attendance can accumulate credits from multiple rules (e.g. travel time
*and* dressing time on the same record). Saving or deleting a rule immediately
reprocesses all unlocked, checked-out attendances in the rule's company.

Domain conditions can filter on any stored field of ``hr.attendance``.

Once allowance lines for a pay period have been reported or transferred
externally, set **Allowance Locked** on the relevant attendance records to
prevent any further changes. Locking can be applied per-record from the form
view or in batch via any standard Odoo list action.

The module installs a daily scheduled action
(*Attendance: Process Allowance Rules*) as a safety net. Under normal
operation this cron is not needed — allowances are kept current by the
reactive write/create triggers — but it guards against records created via
raw SQL or external integrations that bypass the ORM. Locked records are
excluded from the sweep. You can adjust the interval or disable the cron from
Settings > Technical > Scheduled Actions.
