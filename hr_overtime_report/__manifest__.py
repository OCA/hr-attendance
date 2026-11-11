# Copyright 2025 Moduon Team S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0)

{
    "name": "HR Overtime Report",
    "summary": "Overtime report in Employees",
    "version": "18.0.1.0.0",
    "development_status": "Alpha",
    "category": "Human Resources",
    "website": "https://github.com/OCA/hr-attendance",
    "author": "Moduon, Odoo Community Association (OCA)",
    "maintainers": ["rafaelbn", "u0f"],
    "license": "LGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "hr_attendance",
    ],
    "data": [
        "views/hr_attendance_report.xml",
    ],
}
