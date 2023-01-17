# Copyright 2019 ForgeFlow S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Hr Attendance Geolocation",
    "summary": """
        With this module the geolocation of the user is tracked at the
        check-in/check-out step""",
    "version": "16.0.1.0.1",
    "license": "AGPL-3",
    "author": "ForgeFlow S.L., Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/hr-attendance",
    "depends": ["hr_attendance"],
    "data": [
        "views/hr_attendance_views.xml",
        "data/location_data.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "hr_attendance_geolocation/static/src/js/attendance_geolocation.js",
        ],
    },
}
