# Copyright 2023 Hunki Enterprises BV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0)

{
    "name": "Overtime from work calendars",
    "summary": "Calculate overtime records for all work calendar dates",
    "version": "15.0.1.0.0",
    "development_status": "Alpha",
    "category": "Human Resources/Attendances",
    "website": "https://github.com/OCA/hr-attendance",
    "author": "Hunki Enterprises BV, Odoo Community Association (OCA)",
    "maintainers": ["hbrunn"],
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "preloadable": True,
    "post_init_hook": "post_init_hook",
    "depends": [
        "hr_attendance",
    ],
    "data": [
        "data/ir_cron.xml",
    ],
    "demo": [],
}
