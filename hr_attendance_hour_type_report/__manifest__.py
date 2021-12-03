# Copyright 2021 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "HR Attendance hours report",
    "version": "14.0.1.0.0",
    "category": "Human Resources",
    "website": "https://github.com/OCA/hr-attendance",
    "author": "Camptocamp, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "depends": [
        "hr_attendance",
        "hr_holidays_public",
    ],
    "data": [
        "views/res_config_settings.xml",
        "views/hr_attendance.xml",
    ],
    "installable": True,
}
