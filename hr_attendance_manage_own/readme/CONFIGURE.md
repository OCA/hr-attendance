To configure this module:

1.  Go to *Settings \> Users & Companies \> Groups*
2.  Find and select the "User: Manage own attendances" group
3.  Add users to this group to allow them to create and edit their own attendance records

Optionally, you can configure fields that bypass the processed-record write
restriction. This is useful when other modules (e.g. `hr_timesheet_sheet`) need
to write certain fields on attendance records that have already been approved or
refused.

1.  Go to *Settings \> Technical \> Parameters \> System Parameters*
2.  Create a parameter with key `hr_attendance_manage_own.write_bypass_fields`
3.  Set the value to a comma-separated list of field names (e.g. `sheet_id`)