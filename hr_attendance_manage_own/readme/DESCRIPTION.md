This module allows users to create and edit their own attendance records without
requiring attendance manager or officer privileges.

Without this module, regular internal users can only read their own
attendance records. Creating or modifying attendance records requires either the
Attendance Manager role (full access to all records) or the Attendance
Officer role with the employee's attendance manager set to that user.

This module introduces a "User: Manage own attendances" group that grants
create and edit access to the user's own attendance records, with the following
restrictions:

- Users cannot change the overtime status or extra hours of their records.
- When the company's extra hours validation is set to "By Manager", records that
  have been approved or refused cannot be modified or deleted.
