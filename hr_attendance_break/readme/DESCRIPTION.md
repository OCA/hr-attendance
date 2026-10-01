This module lets employees record **breaks** during their attendance (clocked-in)
time, directly from the attendance menu in the top bar ("attendance circle").

A break is always available while an employee is checked in, regardless of what
they are working on. Each break is stored as an individual record with its own
start and end time, so a full working day can contain several breaks (for
example a morning coffee, a lunch break and an afternoon coffee).

For every attendance the module computes:

- **Break Hours**: the total time spent on breaks.
- **Net Worked Hours**: the worked hours minus the breaks.

This is useful to monitor, for compliance purposes, whether employees take breaks
that are too long.
