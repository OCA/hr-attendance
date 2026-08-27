Automatically converts GPS coordinates from attendance check-ins
into readable addresses, improving operational traceability and facilitating
HR audits.

**Main features:**

- **Asynchronous** reverse geocoding via ``queue_job`` (does not block check-in)
- **Cache** of results by normalized coordinates (reduces API calls)
- **Decoupled** and configurable provider (initially Mapbox)
- **Configurable** rounding precision for cache
- Process state visible in attendance form (pending/done/error)


This module requires:

- ``hr_attendance``
- ``hr_attendance_geolocation`` (OCA/hr-attendance)
- ``queue_job`` (OCA/queue)
