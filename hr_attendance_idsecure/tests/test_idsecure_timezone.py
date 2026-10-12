from datetime import datetime

from odoo.tests.common import tagged

from .common import IDSecureTestCommon


@tagged("post_install", "-at_install")
class TestIDSecureTimezone(IDSecureTestCommon):
    """The report endpoint sends wall-clock time with no offset.

    Odoo stores datetimes in UTC, so the appliance timezone has to be applied
    or every event lands off by the local offset.
    """

    def test_default_timezone_is_set(self):
        self.assertTrue(self.device.tz)

    def test_report_time_converted_from_device_timezone(self):
        self.device.tz = "America/Sao_Paulo"
        naive_local = datetime(2026, 8, 21, 11, 55, 12)
        self.assertEqual(
            self.device._parse_event_time({"_parsed_time": naive_local}),
            datetime(2026, 8, 21, 14, 55, 12),
        )

    def test_utc_device_is_not_shifted(self):
        self.device.tz = "UTC"
        naive = datetime(2026, 8, 21, 11, 55, 12)
        self.assertEqual(self.device._parse_event_time({"_parsed_time": naive}), naive)

    def test_other_timezone_uses_its_own_offset(self):
        self.device.tz = "America/Manaus"  # -04, sem horario de verao
        self.assertEqual(
            self.device._parse_event_time(
                {"_parsed_time": datetime(2026, 8, 21, 11, 0, 0)}
            ),
            datetime(2026, 8, 21, 15, 0, 0),
        )

    def test_monitor_epoch_is_absolute(self):
        """The .NET epoch is absolute: the device timezone must not shift it."""
        raw = {"time": "/Date(1766009913000-0300)/"}
        self.device.tz = "America/Sao_Paulo"
        with_sp = self.device._parse_event_time(raw)
        self.device.tz = "UTC"
        with_utc = self.device._parse_event_time(raw)
        self.assertEqual(with_sp, with_utc)
        self.assertEqual(with_sp, datetime(2025, 12, 17, 22, 18, 33))

    def test_parse_dotnet_time_accepts_string(self):
        dt = self.device._parse_dotnet_time("/Date(1766009913000-0300)/")
        self.assertIsInstance(dt, datetime)
        self.assertIsNone(dt.tzinfo)

    def test_parse_dotnet_time_rejects_garbage(self):
        for bad in ("", None, "não é data", "/Date(sem-numero)/"):
            self.assertFalse(self.device._parse_dotnet_time(bad))

    def test_parse_event_time_without_usable_data(self):
        self.assertFalse(self.device._parse_event_time({}))
        self.assertFalse(self.device._parse_event_time({"time": ""}))

    def test_device_time_to_utc_roundtrip(self):
        self.device.tz = "America/Sao_Paulo"
        original = datetime(2026, 3, 15, 7, 30, 0)
        utc = self.device._device_time_to_utc(original)
        self.assertEqual((utc - original).total_seconds(), 3 * 3600)
