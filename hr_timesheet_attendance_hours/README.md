# Timesheet - Attendance Hours

[![License: AGPL-3](https://img.shields.io/badge/licence-AGPL--3-blue.svg)](http://www.gnu.org/licenses/agpl-3.0-standalone.html)

Adds an **Attendance Hours** column to timesheet lines with color-coded status.

## Use Case

The timekeeper logs daily work hours across multiple tasks. This module cross-references
against actual attendance from access control (turnstile / biometric / facial
recognition), highlighting discrepancies with colors.

## Color Logic

Compares total daily timesheet hours vs physical attendance:

- **Green**: Attendance > timesheet + 30min (normal, includes lunch break)
- **Yellow**: Attendance ≈ timesheet (within 30min margin)
- **Red**: Attendance < timesheet (logged more hours than physically present)

Works correctly with multiple tasks per day (3h Task A + 6h Task B = 9h total compared
against attendance).

## Fields Added

- `attendance_hours` — physical presence from `hr.attendance`
- `daily_timesheet_hours` — sum of all timesheet entries for that employee/date

## Dependencies

- `hr_timesheet`
- `hr_attendance`

## Credits

### Authors

- Pop Solutions

### Contributors

- Marcos Méndez

## License

AGPL-3
