==============================
HR Attendance Geolocation Required
==============================

This module enforces mandatory geolocation for employee attendance in Odoo 17. Without this module, employees can clock in and out without providing location data. With this module, employees must enable location services in their browser and have GPS active on their device before they can check in or out.

**Table of contents**

.. contents::
   :local:

Usage
=====

1. Ensure that geolocation services are enabled on the employee’s device.
2. Open *Attendances > Manage Attendances > Kiosk Mode*.
3. Employees attempting to check in or out must allow location access in their browser.
4. If location access is denied, a notification appears instructing the user to enable geolocation.

Credits
=======

Contributors
------------

-  **Álvaro Alonso / Grupo Isonor** <alvaroalonso@grupoisonor.es>

## Licenses

This repository is licensed under [AGPL-3.0](LICENSE).

However, each module can have a totally different license, as long as they adhere to Odoo Community Association (OCA)
policy. Consult each module's `__manifest__.py` file, which contains a `license` key
that explains its license.

----
OCA, or the [Odoo Community Association](http://odoo-community.org/), is a nonprofit
organization whose mission is to support the collaborative development of Odoo features
and promote its widespread use.
