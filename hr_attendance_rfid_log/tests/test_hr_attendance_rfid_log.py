# Copyright 2026 nurzeit.de
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from datetime import datetime, timedelta

from odoo import fields
from odoo.tests.common import TransactionCase
from odoo.tools.misc import mute_logger


class TestHrAttendance(TransactionCase):
    def setUp(self):
        super().setUp()
        self.employee_model = self.env["hr.employee"]
        self.test_employee = self.employee_model.create(
            {
                "name": "Test Employee",
            }  # noqa: E231
        )
        self.rfid_card_code = "5b3f5"
        self.test_employee.rfid_card_code = self.rfid_card_code
        self.log_failed = self.env["hr.attendance.rfid.log"].create(
            {
                "state": "failed",
                "rfid_card_code": self.rfid_card_code,
                "employee_id": self.test_employee.id,
            }
        )

    def test_create_log(self):
        """Valid employee"""
        res = self.employee_model.register_attendance(self.rfid_card_code)
        self.assertTrue("in_rfid_log" in res and res["in_rfid_log"])

    def _get_wizard(self):
        wizard = self.env["hr.attendance.rfid.log.assign.employee"].create(
            {
                "rfid_card_code": self.rfid_card_code,
                # You need to provide the ID of the attendance RFID log here
                "hr_attendance_rfid_log_id": self.log_failed.id,
                "employee_id": self.test_employee.id,
            }
        )
        return wizard

    @mute_logger("odoo.addons.hr_attendance_rfid.models.hr_employee")
    def test_exception_code(self):
        """Checkout is created for a future datetime"""
        self.env["hr.attendance"].create(
            {
                "employee_id": self.test_employee.id,
                "check_in": fields.Date.today(),
                "check_out": fields.Datetime.to_string(
                    datetime.today() + timedelta(hours=8)
                ),
            }
        )
        self.test_employee.write({"attendance_state": "checked_in"})
        res = self.employee_model.register_attendance(self.rfid_card_code)
        self.assertNotEqual(res.get("error_message", ""), "")

    def test_action_open_wizard_assign_employee(self):
        action = self.log_failed.action_open_wizard_assign_employee()
        self.assertEqual(action.get("type"), "ir.actions.act_window")
        self.assertEqual(
            action.get("res_model"), "hr.attendance.rfid.log.assign.employee"
        )
        self.assertEqual(
            action.get("context", {}).get("default_rfid_card_code"), self.rfid_card_code
        )
        self.assertEqual(
            action.get("context", {}).get("default_hr_attendance_rfid_log_id"),
            self.log_failed.id,
        )

    def test_action_set_to_retry_state(self):
        self.assertEqual(self.log_failed.state, "failed")
        self.log_failed.action_set_to_retry_state()
        self.assertEqual(self.log_failed.state, "retry")

    def test_action_set_to_ignore_state(self):
        self.assertEqual(self.log_failed.state, "failed")
        self.log_failed.action_set_to_ignore_state()
        self.assertEqual(self.log_failed.state, "ignore")

    def test_action_retry_now(self):
        self.log_failed.action_set_to_retry_state()
        initial_retry_counter = self.log_failed.retry_counter
        self.log_failed.action_retry_now()
        self.assertEqual(self.log_failed.retry_counter, initial_retry_counter + 1)
        # register_attendance_with_log changes state to success if logged
        self.assertEqual(self.log_failed.state, "success")

    def test_retry_attendance_rfid_log(self):
        self.log_failed.action_set_to_retry_state()
        self.assertEqual(self.log_failed.state, "retry")
        self.env["hr.attendance.rfid.log"]._retry_attendance_rfid_log()
        self.assertEqual(self.log_failed.state, "success")

    def test_purge_attendance_rfid_log(self):
        Log = self.env["hr.attendance.rfid.log"]
        current_date = fields.Datetime.now()

        # Test success logs older than purge_period_success
        log_success_old = Log.create(
            {
                "state": "success",
                "rfid_card_code": self.rfid_card_code,
                "timestamp": current_date - timedelta(days=6),
            }
        )

        # Test failed logs older than purge_period_general
        log_failed_old = Log.create(
            {
                "state": "failed",
                "rfid_card_code": self.rfid_card_code,
                "timestamp": current_date - timedelta(days=41),
            }
        )

        # Test success logs newer than purge_period_success
        log_success_new = Log.create(
            {
                "state": "success",
                "rfid_card_code": self.rfid_card_code,
                "timestamp": current_date - timedelta(days=4),
            }
        )

        Log._purge_attendance_rfid_log()

        self.assertFalse(log_success_old.exists())
        self.assertFalse(log_failed_old.exists())
        self.assertTrue(log_success_new.exists())
        self.assertTrue(
            self.log_failed.exists()
        )  # created today, so newer than 40 days

    def test_wizard_action_assign_employee(self):
        wizard = self._get_wizard()
        # assign to another employee to test changing
        another_employee = self.employee_model.create({"name": "Another Employee"})
        wizard.employee_id = another_employee.id

        # Test assign employee
        res = wizard.action_assign_employee()

        # Check return action
        self.assertEqual(res.get("type"), "ir.actions.act_window_close")

        # Check if RFID card code is assigned to new employee
        self.assertEqual(another_employee.rfid_card_code, self.rfid_card_code)

        # Check if log is updated
        self.assertEqual(self.log_failed.employee_id.id, another_employee.id)
        self.assertEqual(self.log_failed.state, "retry")

    def test_wizard_on_change_employee_id(self):
        wizard = self._get_wizard()

        # Initially, test_employee has rfid_card_code
        self.assertTrue(self.test_employee.rfid_card_code)

        wizard.employee_id = self.test_employee.id
        wizard.on_change_employee_id()
        self.assertTrue("already a RFID card code assigned" in wizard.warning_message)

        # Create an employee without rfid_card_code
        employee_no_rfid = self.employee_model.create({"name": "No RFID Employee"})
        wizard.employee_id = employee_no_rfid.id
        wizard.on_change_employee_id()
        self.assertEqual(wizard.warning_message, "")

    def test_employee_register_attendance_with_existing_log(self):
        # Test passing an existing log to register_attendance
        log_vals = {
            "state": "failed",
            "rfid_card_code": self.rfid_card_code,
            "employee_id": self.test_employee.id,
        }
        existing_log = self.env["hr.attendance.rfid.log"].create(log_vals)
        res = self.employee_model.register_attendance(
            self.rfid_card_code, log=existing_log
        )

        self.assertTrue("in_rfid_log" in res and res["in_rfid_log"])
        self.assertEqual(
            existing_log.state, "success" if res.get("logged") else "failed"
        )

    def test_employee_register_attendance_with_log_freeze_time(self):
        # Test register_attendance_with_log which uses freezegun
        # We need a log with a specific time
        past_time = fields.Datetime.now() - timedelta(hours=5)
        log = self.env["hr.attendance.rfid.log"].create(
            {
                "state": "failed",
                "rfid_card_code": self.rfid_card_code,
                "timestamp": past_time,
            }
        )

        res = self.employee_model.register_attendance_with_log(log)
        self.assertTrue("in_rfid_log" in res and res["in_rfid_log"])

        # In register_attendance_with_log,
        # it registers attendance at the time of the log
        attendance = self.env["hr.attendance"].search(
            [("employee_id", "=", self.test_employee.id)], order="id desc", limit=1
        )
        if attendance:
            # Depending on if it checked in or out, check the time
            time_to_check = (
                attendance.check_in if attendance.check_in else attendance.check_out
            )
            # The time should be very close to past_time
            self.assertTrue(abs((time_to_check - past_time).total_seconds()) < 60)

    def test_purge_attendance_rfid_log_bad_config(self):
        self.env["ir.config_parameter"].sudo().set_param(
            "hr_attendance_rfid_log.purge_period_success", "invalid_int"
        )
        self.env["hr.attendance.rfid.log"]._purge_attendance_rfid_log()

        # Verify it fell back to default
        success_param = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("hr_attendance_rfid_log.purge_period_success")
        )
        self.assertEqual(success_param, "5")

    def test_explicit_retry_log_processing(self):
        # explicitly creates a log record,
        # forces its state to 'retry', and runs the method
        log = self.env["hr.attendance.rfid.log"].create(
            {
                "state": "retry",
                "rfid_card_code": self.rfid_card_code,
                "employee_id": self.test_employee.id,
            }
        )
        self.env["hr.attendance.rfid.log"]._retry_attendance_rfid_log()
        self.assertEqual(log.state, "success")
