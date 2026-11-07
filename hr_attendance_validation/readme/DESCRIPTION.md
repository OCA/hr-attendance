This module adds a validation mechanism to review employee attendance base
on weekly worked hours.

You can choose on the employee's form the `weekly attendance validation`
option to enable this feature. Otherwise employee will fallback
on Odoo daily overtime computation without manager validation.

This module also makes consistent `Requires Allocation` /
`Allow Negative Cap` and `Max allowed hours negative`
settings on leaves type.

This module is based on the `hr_attendance_overtime` module which
mark rows as "overtime" those rows are not due by default as it
could came from possible mist check-out. So manager can decide
to add or not those overtime lines or not and compute or
adjust compensatory/leaves hours to generate.

..note:

    If you are allowing flexible hours - check-in/check-out range
    are bigger than average hours per day - you can generate
    compensatory hours from lines that are not marked as overtime.

Once review is validated attendance lines are locked on that period.

Employees can:

* access to validated sheets to review hours taken account
* see current week hours on check-in view
