# Copyright 2026 Odoo Community Association (OCA)
# License LGPL-3 - See http://www.gnu.org/licenses/lgpl-3.0.html

{
    "name": "HR Attendance Break",
    "version": "19.0.1.0.0",
    "category": "Human Resources",
    "website": "https://github.com/OCA/hr-attendance",
    "author": "Odoo Community Association (OCA)",
    "license": "LGPL-3",
    "installable": True,
    "depends": ["hr_attendance"],
    "data": [
        "security/ir.model.access.csv",
        "security/security.xml",
        "views/hr_attendance_break_view.xml",
        "views/hr_attendance_view.xml",
        "views/res_config_settings_view.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "hr_attendance_break/static/src/components/attendance_menu/**/*",
        ],
        "hr_attendance.assets_public_attendance": [
            "hr_attendance_break/static/src/components/kiosk_break/**/*",
            "hr_attendance_break/static/src/public_kiosk/**/*",
        ],
    },
}
