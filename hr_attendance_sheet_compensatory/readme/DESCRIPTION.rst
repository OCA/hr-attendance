This is based on `hr_attendance_sheet` which add a validation mechanism
to review employee attendance with an auto-lunch calculation.
This allows to generate compensatory hours (allocated leaves) that can
be used later as day off or to regulate credits leaves as
this module is compatible with `hr_holidays_credit` module.

This is based on the `hr_attendance_overtime` module which
mark rows as "overtime" those rows are not due by default
as it could came from possible mist check-out. So manager can
decide to add or not those overtime attendance lines or not and
compute or adjust compensatory/leaves hours to generate.

This module is **incompatible** with hr_attendance_validation
because it implements the same feature and especially generates
errors during hr.attendance validation

..note::

  If you are allowing flexible hours - check-in/check-out range
  are bigger than average hours per day - So you can generate
  compensatory hours from lines that are not marked as overtime.

Once review is validated attendance lines are locked on that period.

At the end managers can check holidays allocation per year and
by employee to make sure allowed employee compensatory hours are
not over.

Employees can:
- access to validated sheets to review hours taken account
- see current week hours on check-in view
