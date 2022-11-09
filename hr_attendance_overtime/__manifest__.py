# Copyright 2021 Pierre Verkest
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Hr Attendance Overtime",
    "summary": "Mark Attendances as overtime.",
    "category": "Human Resources",
    "version": "14.0.1.0.0",
    "license": "AGPL-3",
    "author": "Pierre Verkest, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/hr-attendance",
    "depends": [
        "resource",
        "hr_attendance",
        "hr_attendance_reason",
        "hr_attendance_autoclose",
    ],
    "data": [
        "data/hr_attendance_reason.xml",
        "views/hr_attendance_reason_view.xml",
        "views/hr_attendance_view.xml",
        "views/resource_view.xml",
        "views/assets.xml",
    ],
    "qweb": [
        "static/src/xml/attendance.xml",
    ],
    "maintainers": ["petrus-v"],
    "post_init_hook": "set_week_checkin_checkout_hours_ranges",
}
