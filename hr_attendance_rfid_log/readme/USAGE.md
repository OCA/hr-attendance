**Monitoring RFID Attendances**

To track all attendance data transmitted by your external RFID device,
navigate to **Attendances \> Reporting \> Logs**. This view provides a
complete overview of both successful and failed synchronizations.

- **Successful Syncs:** These records are retained in the log for a
  specific duration, which is managed by an automated scheduled job.
- **Failed Syncs:** Any synchronization errors will be flagged as
  "Failed". Clicking on a failed record opens a troubleshooting wizard
  to help you resolve the issue quickly:
  1.  **Unrecognized Card ("No employee found with card \[x\]"):** Using
      the wizard, you can assign the unregistered card to an employee,
      ignore the clocking event entirely, or prompt Odoo to retry the
      sync.
  2.  **Validation Errors (e.g., Missing Check-out):** This error occurs
      for example if an employee's previous attendance record is
      incomplete (e.g., it has a check-in but no corresponding
      check-out). To resolve this, you must first manually correct the
      previous record. Once you have fixed the underlying issue of a
      failed sync, you can process the pending attendance record in one
      of two ways:
      - **Manual Retry (Recommended):** Click "Retry" within the wizard
        and then the new button that appears in the "Logs" view. This
        instantly syncs the event, allowing you to confirm immediately
        that the clocking was successfully added to the database.
      - **Automatic Retry:** Simply wait for the scheduled cron job to
        automatically retry and process the sync in the background.
