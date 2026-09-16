from unittest.mock import patch

from odoo.exceptions import UserError
from odoo.tests.common import tagged

from .common import IDSecureTestCommon

DEV = "odoo.addons.hr_attendance_idsecure.models.idsecure_device"


@tagged("post_install", "-at_install")
class TestIDSecureFallbacks(IDSecureTestCommon):
    """Degraded-appliance paths: events must never be lost silently."""

    def test_import_with_defaults_when_user_endpoint_is_down(self):
        """A dead user endpoint must not drop the event."""
        with patch.object(type(self.device), "_api_get_user", return_value=None):
            allowed, etype, company = self.device._should_import(4242)
        self.assertTrue(allowed, "evento seria perdido em silêncio")
        self.assertEqual(etype, "employee")
        self.assertEqual(company, self.device.company_id.id)

    def test_user_without_groups_is_skipped(self):
        user = self._make_user_api_response(4243, "Sem Grupo", [])
        with patch.object(type(self.device), "_api_get_user", return_value=user):
            mapping, data = self.device._get_user_mapping(4243)
        self.assertFalse(mapping)
        self.assertTrue(data)

    def test_user_endpoint_failure_returns_no_data(self):
        with patch.object(type(self.device), "_api_get_user", return_value=None):
            self.assertEqual(self.device._get_user_mapping(4244), (False, None))

    def test_group_matched_by_name_when_id_differs(self):
        """Falling back to the name keeps mappings working after an id change."""
        user = self._make_user_api_response(
            4245, "Alguém", [self._make_group(999888, "Gmar", 2)]
        )
        with patch.object(type(self.device), "_api_get_user", return_value=user):
            mapping, _d = self.device._get_user_mapping(4245)
        self.assertEqual(mapping, self.mapping_gmar)

    def test_load_mappings_without_groups_raises(self):
        with patch.object(type(self.device), "_api_get_groups", return_value={}):
            with self.assertRaises(UserError):
                self.device.action_load_mappings()

    def test_load_mappings_ignores_malformed_entries(self):
        payload = {"data": ["lixo", None, self._make_group(3333, "OK", 2)]}
        with patch.object(type(self.device), "_api_get_groups", return_value=payload):
            self.device.action_load_mappings()
        self.assertTrue(
            self.env["idsecure.company.mapping"].search_count(
                [("device_id", "=", self.device.id), ("idsecure_group_id", "=", 3333)]
            )
        )

    def test_test_connection_returns_notification(self):
        with patch.object(
            type(self.device), "_api_login", return_value="tok"
        ), patch.object(type(self.device), "_api_get_access_logs", return_value=[]):
            action = self.device.action_test_connection()
        self.assertEqual(action["type"], "ir.actions.client")
        self.assertEqual(action["tag"], "display_notification")
