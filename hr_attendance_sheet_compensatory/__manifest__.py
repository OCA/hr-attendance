# Copyright 2021 Pierre Verkest
# Copyright 2023 ACSONE SA/NV
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    "name": "HR Attendance Sheet Compensatory",
    "version": "14.0.1.0.3",
    "category": "Human Resources",
    "summary": "Group attendances into attendance sheets.",
    "website": "https://github.com/OCA/hr-attendance",
    "author": "Odoo S.A., Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "installable": True,
    "depends": [
        "hr_attendance",
        "hr_attendance_sheet",
        "hr_attendance_overtime",
        "hr_attendance_reason",
        "hr_attendance_modification_tracking",
        "hr_holidays",
    ],
    "data": [
        "security/hr_attendance_sheet_rule.xml",
        "views/assets.xml",
        "views/hr_attendance.xml",
        "views/hr_attendance_sheet.xml",
        "views/res_config_settings_views.xml",
    ],
}
