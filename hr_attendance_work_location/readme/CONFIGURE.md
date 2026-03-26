To configure work locations for automatic GPS matching:

1. Go to **Employee > Work Locations** and create or edit a location.
2. On the linked address (via **Address**), set the **Latitude** and **Longitude** fields.
   These coordinates are used for proximity matching at check-in and check-out.
3. If a work location should never be auto-assigned (e.g., a "Remote" or "Home"
   category), enable **Exclude from Attendance**. The location remains active and
   visible in the system but is skipped by the GPS matching algorithm.

**Tolerance:** The proximity matching tolerance is configurable per company.
Go to **HR Settings > Attendance** to set the **GPS Tolerance (meters)** value.
The default is 111 meters. Set to 0 to disable automatic matching.

**GPS Tolerance Reference**

The tolerance is specified in meters. A quick reference for common values:

| Meters | Use case                              |
|--------|---------------------------------------|
| 30     | Tight campus / multi-building office  |
| 50     | Single building, clear sky            |
| 111    | Default — safe general value          |
| 200    | Outdoor / rural workers               |
| 500    | Very large industrial sites           |

**Device accuracy matters:** The tolerance must be larger than the GPS
error of the device used for check-in. Typical accuracy ranges:

- **Smartphones:** 3–10 m (good conditions), up to 30 m indoors
- **Laptops (WiFi-based):** 10–50 m
- **Desktops (IP-based):** 1–10 km (not suitable for GPS matching)

If your tolerance is smaller than the device's GPS error, employees
may fail to auto-match even when physically on-site. When in doubt,
start with the default (111 meters) and decrease gradually.

**Integration with time credit rules:** The fields `in_work_location_id` and
`out_work_location_id` on attendance records are standard Odoo domain fields.
When `hr_attendance_time_credit` is also installed, you can use them in credit
rule domain conditions — for example, to grant travel time only when the
employee checked in at a client site:

```
[('in_work_location_id.name', '=', 'Client Site')]
```
