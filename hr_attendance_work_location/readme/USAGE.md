When an employee checks in or out with GPS coordinates (latitude and longitude),
the system automatically resolves the nearest work location and stores it in
the **Check-in Work Location** or **Check-out Work Location** field on the
attendance record.

The matching algorithm:

- Searches all active work locations in the employee's company that are not
  excluded from attendance.
- Filters candidates within the configured tolerance (default 111 meters;
  configurable in **HR Settings > Attendance**).
- Selects the closest match using a flat-earth distance approximation.
- If no location falls within tolerance, the field remains empty.

**Manual override:** If a work location is already set (by the user or a previous
match), the compute does not overwrite it. You can manually select any work
location even when GPS coordinates are absent.

**Exclude from attendance:** Locations marked with **Exclude from Attendance**
are never assigned automatically, but remain available for manual selection.
This is useful for categories like "Remote" or "Home office" where GPS
proximity is not meaningful.

**Tolerance and device accuracy:** The tolerance must be larger than the
GPS error of the device used for check-in. Smartphones typically achieve
3–30 m accuracy. If the tolerance is set too low relative to the device's
accuracy, auto-matching will fail even when the employee is on-site.

**Company assignment:** Attendance records are tied to the company the
employee belonged to at check-in time. If an employee transfers to a
different company, their historical attendance records retain the original
company association.
