{
    "name": "HR Attendance IP Check",
    "summary": """
        Allow attendance check in from specified ip networks only.
    """,
    "author": "Mint System GmbH, Odoo Community Association (OCA)",
    "website": "https://www.mint-system.ch",
    "category": "Technical",
    "version": "15.0.1.1.0",
    "license": "AGPL-3",
    "depends": ["hr_attendance"],
    "data": ["views/attendance_cidr.xml", "security/ir.model.access.csv"],
    "application": False,
    "auto_install": False,
    "images": ["images/screen.png"],
}
