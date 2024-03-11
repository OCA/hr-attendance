# © 2023 initOS GmbH
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Attendance generation for missing days with installed contract",
    "version": "15.0.1.0.0",
    "category": "Hidden",
    "author": "initOS GmbH, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/hr-attendance",
    "license": "AGPL-3",
    "summary": "This modules combines the generation of attendances for working "
    "days without attendance with HR contracts",
    "depends": [
        "hr_contract",
        "hr_attendance_missing_days",
    ],
    "auto_install": True,
    "installable": True,
}
