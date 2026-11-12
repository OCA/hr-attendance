# Copyright 2026 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "HR Attendance Flexible Rest Time",
    "summary": "Deduct rest time from worked hours for flexible-schedule employees",
    "version": "18.0.1.0.0",
    "author": "Quartile, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/hr-attendance",
    "category": "Human Resources/Attendances",
    "license": "AGPL-3",
    "depends": ["hr_attendance"],
    "data": [
        "security/ir.model.access.csv",
        "views/hr_attendance_views.xml",
        "views/resource_calendar_views.xml",
    ],
    "installable": True,
    "maintainers": ["kanda999", "AungKoKoLin1997"],
}
