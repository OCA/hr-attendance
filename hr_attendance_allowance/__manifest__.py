# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
{
    "name": "HR Attendance Allowance",
    "version": "17.0.1.0.0",
    "category": "Human Resources",
    "summary": "Rule-based engine to compute time allowances on attendance records",
    "website": "https://github.com/OCA/hr-attendance",
    "author": "Odoo Community Association (OCA)",
    "license": "LGPL-3",
    "installable": True,
    "depends": ["hr_attendance"],
    "data": [
        "security/ir.model.access.csv",
        "security/hr_attendance_allowance_type_security.xml",
        "security/hr_attendance_allowance_rule_security.xml",
        "security/hr_attendance_allowance_security.xml",
        "data/ir_cron_data.xml",
        "views/hr_attendance_allowance_type_views.xml",
        "views/hr_attendance_allowance_rule_views.xml",
        "views/hr_attendance_allowance_views.xml",
        "views/hr_attendance_views.xml",
    ],
}
