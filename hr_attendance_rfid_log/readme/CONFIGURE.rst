**Configurable Data Purging:** To prevent database bloat, the system features
scheduled actions that purge old logs based on configurable system parameters
(`purge_period_success` and `purge_period_general`).

**Best Practice for Data Retention Policies:** Correctly configure the
`purge_period_success` (e.g., 5 days) and `purge_period_general` (e.g., 40 days)
system parameters. Successful logs don't need to be kept for long since
the actual attendance is recorded, while failed logs should be kept long enough
to be investigated but not indefinitely.
