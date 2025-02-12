# Copyright 2025 Álvaro Alonso Bada - Grupo Isonor
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

{
    "name": "Hr Attendance Report",
    "version": "17.0.1.0.0",
    "category": "Attendance",
    "summary": "Wizard to generate attendance reports in PDF and Excel.",
    "license": "AGPL-3",
    "author": "Grupo Isonor, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/hr-attendance",
    "depends": [
        "hr_attendance",
        "hr",
    ],
    "data": [
        "security/ir.model.access.csv",
        "report/employee_attendance_report_wizard_form.xml",
        "report/employee_attendance_report_wizard_view.xml",
        "wizard/employee_attendance_report_wizard_view.xml",
        "wizard/excel_report.xml",
        "report/report_menu.xml",
    ],
    "demo": [],
    "auto_install": False,
    "application": True,
    "installable": True,
}
