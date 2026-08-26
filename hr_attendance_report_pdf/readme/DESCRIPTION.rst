This module adds a wizard to generate configurable attendance reports and
export them to PDF. It is aimed at users who need clear listings per employee
or per department, with options to control the level of detail, how empty
days are shown, and the hours format.

How to use the wizard

- Open the Report Wizard from the Attendance Wizards menu.
- Fill the date range: "Date from" and "Date to".
- Choose the report scope:
	- `Employee`: select one or more employees for individual reports.
	- `Department`: select one or more departments for departmental reports.
- Other options available in the wizard:
	- "Include open entries": enable to show attendance entries without an
		exit time. Open entries are marked as "Open" and their duration is
		calculated up to the report end date or the current time.
	- "Mode": choose between "Summary" or "Detailed".
		- Summary: shows totals per day and per employee (good for quick reviews).
		- Detailed: lists each attendance record (check-in/check-out) with its
			duration.
	- "Show empty days": enable to include days in the range with no records
		(they appear as 0h). By default they are hidden for a more compact report.
	- "Hours format": select how hours are displayed in the report:
		- "HH:MM" (e.g. 08:30)
		- "Decimals" (e.g. 8.50)

Behavior by report type

- Individual reports: focused on one or several employees; in Summary mode
	they show daily and weekly totals; in Detailed mode they show every
	attendance record.
- Departmental reports: group records by department and show subtotals per
	department and overall totals. You can combine employee filters within the
	department if needed.
- Open entries: when included, the report clearly flags open rows and
	computes their duration using the report end date.

Recommendations

- For audits or detailed checks, use "Detailed" mode and enable "Show empty days".
- For monthly summaries or dashboards, use "Summary" mode and the decimal
	format if you need to sum hours quickly.
