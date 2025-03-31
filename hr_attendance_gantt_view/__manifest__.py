# Copyright 2025 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "HR Attendance Gantt View",
    "summary": """
        This module adds the gantt view as an option to display attendances""",
    "license": "AGPL-3",
    "author": "Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/hr-attendance",
    "category": "Human Resources",
    "version": "16.0.1.0.0",
    "depends": ["hr_attendance"],
    "data": [
        "views/hr_attendance_views.xml",
    ],
}
