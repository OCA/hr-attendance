- Ensure employee `working hours` (the week resource calendar) are properly set.

- Check bellow the `Weekly Attendance Validation` boolean on the same employee form
  to use validation sheet or not for this employee.

- Make sure proper Extra Hours leave types settings:

  - `Deduct Extra Hours`: Use hr.attendance.overtime to compute extra hours
    assigned and taken by employees.
  - `Requires Allocation`: Used to control employees credit hours based
    on accumulated compensatory hours. And allow extra allocations !
  - `Allow Negative Cap`: Allow negative hours to be taken.
  - `Max allowed hours negative`: amount of hours allowed to be taken
    negative.


- You can ignore some leaves in validation sheet by choosing `Worked Time` as
  *kind of time Off*. For instance it can be useful if you manage employee 
  remote days using `hr.leave` in such case you want to ignore those lines.

- configure public holidays to take care of it while computing the
  theoretical week time

- once all leaves and attendances has been recorded you can generate
  leave reviews by setting up a cron job running every monday morning to
  generate the previous week with the following code on
  hr.attendance.validation.sheet model:

      model.generate_reviews()
