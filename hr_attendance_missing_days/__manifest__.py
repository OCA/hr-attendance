# © 2023 initOS GmbH
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Attendance generation for missing days",
    "version": "17.0.1.0.0",
    "category": "Hidden",
    "author": "initOS GmbH, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/hr-attendance",
    "license": "AGPL-3",
    "summary": "This modules generates attendances for working days without attendance",
    "depends": [
        "hr_attendance_reason",
    ],
    "data": [
        "data/hr_attendance_reason.xml",
        "data/ir_cron.xml",
        "views/res_config_settings_views.xml",
    ],
    "installable": True,
}
