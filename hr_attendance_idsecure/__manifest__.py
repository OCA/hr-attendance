{
    "name": "HR Attendance - iDSecure Integration",
    "version": "16.0.2.1.0",
    "category": "Human Resources/Attendances",
    "summary": "Automatic attendance from iDSecure (ControliD) access control",
    "author": "Pop Solutions, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/hr-attendance",
    "license": "AGPL-3",
    "depends": [
        "hr_attendance",
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/ir_cron.xml",
        "views/idsecure_access_log_views.xml",
        "views/idsecure_company_mapping_views.xml",
        "wizard/idsecure_historical_sync_wizard_views.xml",
        "views/idsecure_device_views.xml",
        "views/hr_employee_views.xml",
        "wizard/idsecure_sync_wizard_views.xml",
        "views/menu.xml",
    ],
    "external_dependencies": {
        "python": ["requests"],
    },
    "installable": True,
    "application": False,
    "auto_install": False,
}
