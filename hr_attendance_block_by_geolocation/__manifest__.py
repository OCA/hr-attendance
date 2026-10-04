{
    "name": "HR Attendance Block by Geolocation",
    "version": "18.0.1.0.0",
    "category": "Human Resources",
    "summary": "Restricts HR attendance input based on employee location.",
    "author": "APSL - Nagarro, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/hr-attendance",
    "depends": ["hr_attendance", "hr"],
    "data": [
        "security/ir.model.access.csv",
        "views/hr_attendance_location.xml",
        "views/hr_employee.xml",
    ],
    "license": "AGPL-3",
    "maintainers": ["mpascuall"],
}
