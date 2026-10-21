This module provides an intermediary logging layer between external RFID
terminals and Odoo's hr.attendance model, capturing raw clocking events
to prevent them from accumulating on devices. It features an UI
(displaying both successful and failed syncs) coupled with a transient
wizard to troubleshoot database sync errors and map new RFID cards to
employees. Includes a scheduled cron job to automatically purge old
records, utilizing separate retention periods for successful versus
failed events.
