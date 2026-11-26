- `hr_attendance_rest_time_included` (Tecnativa, up to 18.0) records breaks
  with the same check out / check in flow, but in a model of its own and
  always as paid time. Once it is migrated to 19.0, it could store its breaks
  in `hr.attendance.break`, using a paid break type, so both modules share the
  same data.
- Starting a break directly from the kiosk without picking a reason, through a
  default break reason, could reduce the number of taps further.
