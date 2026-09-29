from odoo import models


class HrAttendanceReport(models.AbstractModel):
    _name = "report.hr_attendance_report_pdf.report_attendance_template"
    _description = "Report Attendance"

    def _get_report_values(self, docids, data=None):
        service = self.env["hr.attendance.report.service"]
        report_data = service._prepare_report_values(data)

        return {
            "doc_ids": docids,
            "doc_model": "hr.attendance",
            **report_data,
            "tz": self.env.user.tz,
        }
