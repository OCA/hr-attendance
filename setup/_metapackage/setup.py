import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo-addons-oca-hr-attendance",
    description="Meta package for oca-hr-attendance Odoo addons",
    version=version,
    install_requires=[
        'odoo-addon-hr_attendance_autoclose>=16.0dev,<16.1dev',
        'odoo-addon-hr_attendance_calendar_view>=16.0dev,<16.1dev',
        'odoo-addon-hr_attendance_geolocation>=16.0dev,<16.1dev',
        'odoo-addon-hr_attendance_reason>=16.0dev,<16.1dev',
        'odoo-addon-hr_attendance_report_theoretical_time>=16.0dev,<16.1dev',
        'odoo-addon-hr_attendance_rfid>=16.0dev,<16.1dev',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
        'Framework :: Odoo :: 16.0',
    ]
)
