Several types of attendance-linked time credits appear in European collective
agreements (*convenios colectivos*, *conventions collectives*, Tarifverträge)
that are neither overtime nor leave: they are supplementary credits with their
own rate, possible cap, and separate accounting line. Common examples:

- **Travel time** (*tiempo de desplazamiento*, *temps de trajet excédentaire*,
  *Wegezeit*) — time spent travelling outside scheduled hours, often credited
  at a fraction of the normal rate.
- **Dressing / changing time** (*tiempo de vestuario*, *temps d'habillage*,
  *Umkleidezeit*) — fixed minutes per shift for mandatory uniform changes, well
  established by case law (BAG, Cour de cassation).
- **Paid breaks** (*pausa retribuida*, *temps de pause*) — fixed credits per
  shift required by many sector agreements (metal, hospitality, healthcare).
- **Setup / preparation time** (*Rüstzeit*) — proportional or fixed credit for
  preparation work before the shift clock starts.
- **Shower / wash time** (*Waschzeit*, *temps de douche*) — fixed credit for
  hazardous or dirty roles.

Treating any of these as overtime pollutes legal overtime thresholds; treating
them as leave conflates rest entitlement with a work-related credit. In
practice, HR, payroll, and auditors expect them in separate ledger lines.

**Why not OCA hr_attendance_overtime?**

``hr_attendance_overtime`` computes time worked beyond a scheduled shift and
splits attendance records accordingly. That model does not fit supplementary
credits: an employee can travel *during* scheduled hours, dressing time applies
regardless of shift length, and the credit is often a fraction of the duration
rather than a 1:1 addition. The module also depends on
``hr_attendance_reason`` and ``hr_attendance_autoclose``, pulling in a workflow
that is not needed here.

**Why not core Odoo overtime?**

Odoo's built-in overtime is a straight delta between scheduled and actual
hours. There is no rule engine to apply conditional logic, and the two
approaches would produce conflicting totals on the same attendance.

**Why not hr.leave?**

Leave carries statutory meaning (rest, recovery) and its own accrual and
approval workflow. Mixing supplementary credits into leave balances creates
reporting problems and may conflict with local regulation on leave accounting.

**What this module does instead**

It attaches a lightweight rule engine to attendance records. Each rule
specifies a condition (Odoo domain or server-action code) and a base minutes
value, then applies a **rate multiplier** and an optional **minutes cap** before
recording the result as a typed allowance line. Common patterns — fixed
dressing-time credits, half-rate travel time, per-day caps — work with plain
domain rules. More specific logic (distance thresholds, destination-based
rates, weekday/weekend conditions) can be handled with server-action code on
the rule.

Allowances are recomputed reactively (on save) so the record is never stale.
Lines can be locked per attendance once a pay period is closed, preventing
retroactive changes.

The module stops at tracking and attribution. Conversion to pay, compensatory
time-off, or salary supplement requires a payroll integration that is out of
scope here and varies too much across jurisdictions to be generic.
