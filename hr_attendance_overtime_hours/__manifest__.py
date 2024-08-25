# Copyright 2023 Janik von Rotz <janik.vonrotz@mint-system.ch>
# Copyright 2024 Camptocamp
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    "name": "HR Attendance Overtime Hours",
    "summary": """
        Show planned and worked hours in overtime view.
    """,
    "author": "Mint System GmbH, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/hr-attendance",
    "category": "Human Resources",
    "version": "17.0.1.0.0",
    "license": "AGPL-3",
    "depends": ["hr_attendance"],
    "data": ["views/hr_attendance_overtime.xml"],
    "installable": True,
    "application": False,
    "auto_install": False,
    "images": ["images/screen.png"],
}
