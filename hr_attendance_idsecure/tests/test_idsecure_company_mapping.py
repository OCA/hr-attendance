from psycopg2 import IntegrityError

from odoo.tests.common import tagged
from odoo.tools import mute_logger

from .common import IDSecureTestCommon


@tagged("post_install", "-at_install")
class TestIDSecureCompanyMapping(IDSecureTestCommon):
    def test_mapping_types(self):
        self.assertEqual(self.mapping_mcp.employee_type, "employee")
        self.assertEqual(self.mapping_gmar.employee_type, "freelancer")
        self.assertFalse(self.mapping_visitors.import_attendance)

    def test_cascade_delete(self):
        ids = self.device.mapping_ids.ids
        self.device.unlink()
        self.assertFalse(
            self.env["idsecure.company.mapping"].search([("id", "in", ids)])
        )

    def test_idsecure_id_unique(self):
        with self.assertRaises(IntegrityError), mute_logger("odoo.sql_db"):
            with self.cr.savepoint():
                self.env["hr.employee"].create(
                    {"name": "Dupe", "idsecure_id": 1001, "company_id": self.company.id}
                )

    def test_idsecure_id_zero_not_unique(self):
        e1 = self.env["hr.employee"].create(
            {"name": "Zero1", "idsecure_id": 0, "company_id": self.company.id}
        )
        e2 = self.env["hr.employee"].create(
            {"name": "Zero2", "idsecure_id": 0, "company_id": self.company.id}
        )
        self.assertTrue(e1 and e2)

    def test_log_count(self):
        for i in range(3):
            self.env["idsecure.access.log"].create(
                {
                    "device_id": self.device.id,
                    "id_log": 80000 + i,
                    "employee_id": self.employee_mcp.id,
                    "employee_name_raw": "Test",
                    "id_user": 1001,
                    "event_time": "2026-03-11 10:00:00",
                    "direction": "entry",
                    "event_code": 7,
                    "event_name": "Test",
                    "device_name": "c1",
                    "area_name": "T",
                    "state": "done",
                }
            )
        self.employee_mcp._compute_idsecure_log_count()
        self.assertEqual(self.employee_mcp.idsecure_log_count, 3)
