# Copyright 2021 Pierre Verkest
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Hr Attendance Validation",
    "summary": "Employee attendance validation.",
    "category": "Human Resources",
    "version": "17.0.1.0.0",
    "license": "AGPL-3",
    "author": "Pierre Verkest, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/hr-attendance",
    "depends": [
        "hr_attendance",
        "hr_attendance_overtime",
        "hr_attendance_reason",
        "hr_attendance_modification_tracking",
        "hr_holidays",
        "hr_holidays_public",
        "hr_holidays_attendance",
    ],
    "data": [
        "views/hr_attendance_overtime.xml",
        "views/hr_attendance_validation.xml",
        "views/hr_attendance.xml",
        "views/hr_employee.xml",
        "security/ir.model.access.csv",
        "security/ir.rule.xml",
        "data/ir_cron.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "hr_attendance_validation/static/src/**/*",
        ],
    },
    "maintainers": ["petrus-v"],
}
