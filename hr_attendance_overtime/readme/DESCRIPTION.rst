Mark Attendances as overtime according works week employee configuration
to track times done outside the theoretical work times.

At check-out time the attendance line can be split in order to help manager
with employee presence reviews and compute compensatory hours.

With this module:

* Employee can visualize plan open work times

  .. image:: ../static/img/my_attendance.png

  The check-in/check-out button has different colors according
  the current state, employee is early, on time, late.

* You can configure theoretical check-in/check-out hours ranges on employee works
  week.

* While employee check-out following rules are applied on the closed attendance line:

  * Checking rules are:

    * check-in before starting ranges will create two attendances:

      * The first one will be marked as overtime and stopped at the beginning of the
        starting range, an earlier reason will be add.
      * The second will start at the end of the first one.

    * check-in in the starting range will open attendance as normal
    * check-after the starting range will open attendances as normal adding
      a late reason

  * Check out rules

    * Check-out before check-out hours range will marked the attendance as leave earlier
    * Check-out in the given range will close the attendance as normal
    * Check-out after the range will generate 2 attendance

      * a normal one that terminate at the end of the range
      * an overtime one that start from the end of range to the check-out time
        a late reason is added as well

* Auto close rules: We suggest to plan an auto close ir.cron after each
  work time attendance basically one between the
  morning and afternoon and one at the end of the day.
  Previous check-out rules described above will be applied with the
  auto-close module reason using the ir cron execution time. If no
  theoretical work time found for open hr attendance a fallback to the
  auto-close module rules are applied.


This module is used by `hr_attendance_validation` in order to helps
manager review weeks hours and generate compensatoires hours per
employee.
