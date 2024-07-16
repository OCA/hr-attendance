# Copyright 2024 Moduon Team S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0)

{
    "name": "Update Overtime from HR Contract",
    "summary": "Update Overtime from HR Contract",
    "version": "16.0.1.0.0",
    "development_status": "Alpha",
    "category": "Human Resources/Contracts",
    "website": "https://github.com/OCA/hr-attendance",
    "author": "Moduon, Odoo Community Association (OCA)",
    "maintainers": ["Shide", "rafaelbn"],
    "license": "LGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "hr_contract",
        "hr_attendance",
    ],
    "data": [
        "data/hr_contract_history_data.xml",
        "views/hr_contract_history_view.xml",
        "views/hr_contract_view.xml",
    ],
}
