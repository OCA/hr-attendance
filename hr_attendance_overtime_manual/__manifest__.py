# © 2023 initOS GmbH
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "HR Attendance Overtime Manual",
    "version": "15.0.1.0.0",
    "category": "Hidden",
    "author": "initOS GmbH, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/hr-attendance",
    "license": "AGPL-3",
    "summary": "Allows adding manual overtime records",
    "depends": [
        "hr_attendance",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/hr_attendance_overtime_views.xml",
        "views/hr_employee_views.xml",
        "wizard/hr_attendance_overtime_manual_wizard_views.xml",
    ],
    "installable": True,
}
