import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo-addons-oca-hr-attendance",
    description="Meta package for oca-hr-attendance Odoo addons",
    version=version,
    install_requires=[
        'odoo-addon-hr_attendance_autoclose>=15.0dev,<15.1dev',
        'odoo-addon-hr_attendance_calendar_view>=15.0dev,<15.1dev',
        'odoo-addon-hr_attendance_geolocation>=15.0dev,<15.1dev',
        'odoo-addon-hr_attendance_reason>=15.0dev,<15.1dev',
        'odoo-addon-hr_attendance_report_theoretical_time>=15.0dev,<15.1dev',
        'odoo-addon-hr_attendance_rfid>=15.0dev,<15.1dev',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
        'Framework :: Odoo :: 15.0',
    ]
)
