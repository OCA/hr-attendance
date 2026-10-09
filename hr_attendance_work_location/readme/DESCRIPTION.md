This module enhances HR Attendance by enabling work location tracking on
employee attendance records. It supports two modes:

- **Automatic (GPS):** Work location is resolved from GPS coordinates
  at check-in and check-out time.
- **Manual (Selector):** After employee identification (barcode scan or
  manual selection), an intermediate screen appears where the employee
  selects their work location. The selected location is displayed in
  read-only on the greeting screen.

In manual mode, the work location selector is available in the backend
systray attendance popup before **both check-in and check-out**. The
selected location is stored in the **Check-in Work Location** or
**Check-out Work Location** field on the attendance record accordingly.
The selector is editable at all times, so employees can review or change
the location before checking in or out.
