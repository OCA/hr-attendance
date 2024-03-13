# Copyright 2023 Hunki Enterprises BV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0)

{
    "name": "Work breaks",
    "summary": "Allows employees to manage their work breaks",
    "version": "15.0.1.0.0",
    "development_status": "Beta",
    "category": "Human Resources/Attendances",
    "website": "https://github.com/OCA/hr-attendance",
    "author": "Hunki Enterprises BV, Odoo Community Association (OCA), verdigado eG",
    "maintainers": ["hbrunn"],
    "license": "AGPL-3",
    "depends": [
        "hr_attendance",
        "hr_attendance_reason",
    ],
    "data": [
        "security/hr_attendance_break.xml",
        "security/ir.model.access.csv",
        "data/hr_attendance_reason.xml",
        "data/mail_activity_type.xml",
        "data/mail_template.xml",
        "data/ir_actions_server.xml",
        "data/ir_cron.xml",
        "views/hr_attendance.xml",
        "views/hr_attendance_break.xml",
        "views/hr_attendance_break_threshold.xml",
        "views/hr_attendance_reason.xml",
        "views/hr_attendance_report.xml",
        "views/res_config_settings.xml",
    ],
    "demo": [
        "demo/res_company.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "hr_attendance_break/static/src/js/hr_attendance_break.js",
            "hr_attendance_break/static/src/scss/hr_attendance_break.scss",
        ],
        "web.assets_qweb": [
            "hr_attendance_break/static/src/xml/hr_attendance_break.xml",
        ],
    },
}
