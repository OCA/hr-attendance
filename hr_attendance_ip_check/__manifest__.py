# Copyright 2024 Janik von Rotz <janik.vonrotz@mint-system.ch>
# Copyright 2024 Camptocamp
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    "name": "HR Attendance IP Check",
    "summary": """
        Allow attendance check in from specified ip networks only.
    """,
    "author": "Mint System GmbH, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/hr-attendance",
    "category": "Technical",
    "version": "17.0.1.0.0",
    "license": "AGPL-3",
    "depends": ["hr_attendance"],
    "data": ["views/attendance_cidr.xml", "security/ir.model.access.csv"],
    "application": False,
    "auto_install": False,
    "images": ["images/screen.png"],
}
