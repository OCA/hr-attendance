# Copyright 2026 Odoo Community Association (OCA)
# License LGPL-3 - See http://www.gnu.org/licenses/lgpl-3.0.html

{
    "name": "HR Attendance Break",
    "version": "19.0.1.0.0",
    "category": "Human Resources",
    "website": "https://github.com/OCA/hr-attendance",
    "author": "Odoo Community Association (OCA)",
    "license": "LGPL-3",
    "depends": ["hr_attendance_reason"],
    "data": [
        "security/ir.model.access.csv",
        "security/security.xml",
        "data/hr_attendance_break_type_data.xml",
        "views/hr_attendance_break_type_view.xml",
        "views/hr_attendance_break_view.xml",
        "views/hr_attendance_reason_view.xml",
        "views/hr_attendance_view.xml",
        "views/res_config_settings_view.xml",
    ],
    "demo": [
        "demo/hr_attendance_reason_demo.xml",
    ],
}
