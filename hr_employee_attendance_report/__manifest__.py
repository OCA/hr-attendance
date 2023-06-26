{
    "name": "HR Employee Attendance Report",
    "summary": """
        Attendance and leave report.
    """,
    "author": "Mint System GmbH, Odoo Community Association (OCA)",
    "website": "https://www.mint-system.ch",
    "category": "Human Resources",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "depends": ["hr_attendance", "hr_holidays", "hr_holidays_remaining_leaves"],
    "data": [
        "report/hr_employee_report.xml",
        "report/res_users_report.xml",
        "security/ir.model.access.csv",
        "wizard/select_period.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
    "images": ["images/screen.png"],
}
