# Copyright 2026 Binhex
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from contextlib import contextmanager
from types import SimpleNamespace
from unittest.mock import patch

from odoo import http

from odoo.addons.base.tests.common import BaseCommon
from odoo.addons.hr_attendance.controllers.main import HrAttendance as CoreHrAttendance
from odoo.addons.hr_attendance_work_location.controllers.main import (
    HrAttendance as WorkLocationHrAttendance,
)


@contextmanager
def _http_request(env, **params):
    """A stand-in kiosk request pushed on ``odoo.http._request_stack``.

    ``params`` models what ``ir.http._dispatch`` binds: the raw params the
    dispatcher hands the endpoint.
    """
    fake = SimpleNamespace(
        env=env,
        params=params,
        httprequest=SimpleNamespace(
            cookies={}, user_agent=SimpleNamespace(browser="test-browser")
        ),
        geoip=SimpleNamespace(
            city=SimpleNamespace(name="TestCity"),
            country=SimpleNamespace(name="TestCountry"),
            continent=SimpleNamespace(name="TestContinent"),
            location=SimpleNamespace(latitude=0.0, longitude=0.0),
            ip="127.0.0.1",
        ),
    )
    fake.update_context = lambda **overrides: setattr(
        fake, "env", fake.env(context=dict(fake.env.context, **overrides))
    )
    http._request_stack.push(fake)
    try:
        yield fake
    finally:
        http._request_stack.pop()


class _StubSibling(CoreHrAttendance):
    """A sibling module's routed override, mimicking ``hr_attendance_displacement``.

    It owns ``sibling_flag`` and hands ``work_location_id`` down only when set,
    exactly like the real sibling, so it can be placed above or below the
    work-location controller in a synthetic MRO.
    """

    seen = None

    def manual_selection_with_geolocation(
        self,
        token,
        employee_id,
        pin_code,
        latitude=False,
        longitude=False,
        sibling_flag=False,
        work_location_id=False,
    ):
        _StubSibling.seen = sibling_flag
        call = {"latitude": latitude, "longitude": longitude}
        if work_location_id:
            call["work_location_id"] = work_location_id
        return super().manual_selection_with_geolocation(
            token, employee_id, pin_code, **call
        )


class _StubGeoGuard(CoreHrAttendance):
    """A sibling below work_location that refuses without GPS, mimicking
    ``hr_attendance_geolocation_required``.
    """

    def manual_selection_with_geolocation(
        self, token, employee_id, pin_code, latitude=False, longitude=False, **kwargs
    ):
        if not latitude or not longitude:
            return {"error": "geolocation_required"}
        return super().manual_selection_with_geolocation(
            token, employee_id, pin_code, latitude=latitude, longitude=longitude
        )


# Keep the stubs out of the routing map: Odoo merges every controller leaf whose
# module is installed, so a stub left in this addon's namespace would become a
# real (order-shifting) endpoint of the kiosk route.
_StubSibling.__module__ = "hr_attendance_work_location_test_stub"
_StubGeoGuard.__module__ = "hr_attendance_work_location_test_stub"


def _merged(*bases):
    """A synthetic merged controller in the given load order.

    ``__module__`` is pinned outside ``odoo.addons`` so the class is not picked
    up as a real controller leaf by ``_generate_routing_rules``.
    """
    controller = type("MergedController", bases, {})
    controller.__module__ = "hr_attendance_work_location_test_stub"
    return controller


class TestWorkLocationControllerComposition(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.company.attendance_kiosk_key = "wl-composition-token"
        cls.company.work_location_mode = "manual"
        cls.company.work_location_required = False
        cls.company.attendance_kiosk_use_pin = False
        cls.employee = cls.env["hr.employee"].create(
            {"name": "WL Composition Employee", "company_id": cls.company.id}
        )
        address = cls.env["res.partner"].create({"name": "WL Composition Address"})
        cls.location = cls.env["hr.work.location"].create(
            {
                "name": "WL Composition Office",
                "company_id": cls.company.id,
                "address_id": address.id,
                "location_type": "office",
            }
        )
        cls.token = cls.company.attendance_kiosk_key

    def test_manual_selection_delegates_to_super(self):
        """The override must run the rest of the chain, not reimplement it."""
        with patch.object(
            CoreHrAttendance,
            "manual_selection_with_geolocation",
            autospec=True,
            return_value={"id": self.employee.id},
        ) as core_method:
            with _http_request(self.env):
                WorkLocationHrAttendance().manual_selection_with_geolocation(
                    self.token,
                    self.employee.id,
                    False,
                    work_location_id=self.location.id,
                )
        core_method.assert_called_once()

    def test_systray_attendance_delegates_to_super(self):
        with patch.object(
            CoreHrAttendance,
            "systray_attendance",
            autospec=True,
            return_value={"id": self.employee.id},
        ) as core_method:
            with _http_request(self.env):
                WorkLocationHrAttendance().systray_attendance(
                    work_location_id=self.location.id
                )
        core_method.assert_called_once()

    def test_geolocation_guard_below_still_runs(self):
        """A sibling guard placed below work_location is reached, not truncated."""
        controller = _merged(WorkLocationHrAttendance, _StubGeoGuard)
        with _http_request(self.env):
            response = controller().manual_selection_with_geolocation(
                self.token, self.employee.id, False, work_location_id=self.location.id
            )
        self.assertEqual(response.get("error"), "geolocation_required")

    def test_topmost_work_location_forwards_sibling_params(self):
        """With work_location first in the MRO, a sibling below still gets its param."""
        _StubSibling.seen = None
        controller = _merged(WorkLocationHrAttendance, _StubSibling)
        with _http_request(self.env):
            controller().manual_selection_with_geolocation(
                self.token,
                self.employee.id,
                False,
                sibling_flag="kept",
                work_location_id=self.location.id,
            )
        self.assertEqual(_StubSibling.seen, "kept")

    def test_work_location_below_a_sibling_consumes_its_kwarg(self):
        """With a sibling first in the MRO, the forwarded work_location_id lands."""
        _StubSibling.seen = None
        controller = _merged(_StubSibling, WorkLocationHrAttendance)
        with _http_request(self.env):
            controller().manual_selection_with_geolocation(
                self.token,
                self.employee.id,
                False,
                sibling_flag="kept",
                work_location_id=self.location.id,
            )
        self.assertEqual(_StubSibling.seen, "kept")
        attendance = self.employee.sudo().last_attendance_id
        self.assertEqual(attendance.in_work_location_id, self.location)

    def test_work_location_required_blocks_before_delegating(self):
        self.company.work_location_required = True
        try:
            with patch.object(
                CoreHrAttendance, "manual_selection_with_geolocation", autospec=True
            ) as core_method:
                with _http_request(self.env):
                    response = (
                        WorkLocationHrAttendance().manual_selection_with_geolocation(
                            self.token, self.employee.id, False
                        )
                    )
            self.assertEqual(response.get("error"), "work_location_required")
            core_method.assert_not_called()
        finally:
            self.company.work_location_required = False

    def test_automatic_mode_ignores_the_requirement(self):
        """Automatic mode resolves the location from GPS after the punch, so a
        requirement on the request would refuse every punch."""
        self.company.write(
            {"work_location_mode": "automatic", "work_location_required": True}
        )
        try:
            with patch.object(
                CoreHrAttendance,
                "manual_selection_with_geolocation",
                autospec=True,
                return_value={"id": self.employee.id},
            ) as core_method:
                with _http_request(self.env):
                    response = (
                        WorkLocationHrAttendance().manual_selection_with_geolocation(
                            self.token, self.employee.id, False
                        )
                    )
            self.assertFalse(response.get("error"))
            core_method.assert_called_once()
        finally:
            self.company.write(
                {"work_location_mode": "manual", "work_location_required": False}
            )

    def test_automatic_mode_systray_ignores_the_requirement(self):
        self.company.write(
            {"work_location_mode": "automatic", "work_location_required": True}
        )
        try:
            with patch.object(
                CoreHrAttendance,
                "systray_attendance",
                autospec=True,
                return_value={"id": self.employee.id},
            ) as core_method:
                with _http_request(self.env):
                    response = WorkLocationHrAttendance().systray_attendance()
            self.assertFalse(response.get("error"))
            core_method.assert_called_once()
        finally:
            self.company.write(
                {"work_location_mode": "manual", "work_location_required": False}
            )


class _StubBadgeSibling(CoreHrAttendance):
    """A sibling override of the badge route that owns ``sibling_flag``."""

    seen = None

    def scan_barcode(self, token, barcode, sibling_flag=False, work_location_id=False):
        _StubBadgeSibling.seen = sibling_flag
        call = {"work_location_id": work_location_id} if work_location_id else {}
        return super().scan_barcode(token, barcode, **call)


_StubBadgeSibling.__module__ = "hr_attendance_work_location_test_stub"


class TestWorkLocationBadgeRoute(BaseCommon):
    """The core badge route honours the manual-mode requirement and keeps the
    location a sibling kiosk screen collected before the punch."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.company.attendance_kiosk_key = "wl-badge-token"
        cls.company.work_location_mode = "manual"
        cls.company.work_location_required = False
        cls.employee = cls.env["hr.employee"].create(
            {
                "name": "WL Badge Employee",
                "company_id": cls.company.id,
                "barcode": "WLBADGE01",
            }
        )
        address = cls.env["res.partner"].create({"name": "WL Badge Address"})
        cls.location = cls.env["hr.work.location"].create(
            {
                "name": "WL Badge Office",
                "company_id": cls.company.id,
                "address_id": address.id,
                "location_type": "office",
            }
        )
        cls.token = cls.company.attendance_kiosk_key

    def test_badge_refused_without_location_in_manual_required(self):
        self.company.work_location_required = True
        try:
            with patch.object(
                CoreHrAttendance, "scan_barcode", autospec=True
            ) as core_method:
                with _http_request(self.env):
                    response = WorkLocationHrAttendance().scan_barcode(
                        self.token, "WLBADGE01"
                    )
            self.assertEqual(response.get("error"), "work_location_required")
            core_method.assert_not_called()
        finally:
            self.company.work_location_required = False

    def test_badge_records_the_location(self):
        with _http_request(self.env):
            response = WorkLocationHrAttendance().scan_barcode(
                self.token, "WLBADGE01", work_location_id=self.location.id
            )
        self.assertEqual(response.get("employee_name"), self.employee.name)
        attendance = self.employee.sudo().last_attendance_id
        self.assertEqual(attendance.in_work_location_id, self.location)

    def test_badge_in_automatic_mode_ignores_the_requirement(self):
        self.company.write(
            {"work_location_mode": "automatic", "work_location_required": True}
        )
        try:
            with _http_request(self.env):
                response = WorkLocationHrAttendance().scan_barcode(
                    self.token, "WLBADGE01"
                )
            self.assertEqual(response.get("employee_name"), self.employee.name)
        finally:
            self.company.write(
                {"work_location_mode": "manual", "work_location_required": False}
            )

    def test_badge_composes_with_a_sibling_in_either_order(self):
        for bases in (
            (WorkLocationHrAttendance, _StubBadgeSibling),
            (_StubBadgeSibling, WorkLocationHrAttendance),
        ):
            _StubBadgeSibling.seen = None
            self.employee.sudo().attendance_ids.unlink()
            controller = _merged(*bases)
            with _http_request(self.env):
                controller().scan_barcode(
                    self.token,
                    "WLBADGE01",
                    sibling_flag="kept",
                    work_location_id=self.location.id,
                )
            self.assertEqual(_StubBadgeSibling.seen, "kept")
            attendance = self.employee.sudo().last_attendance_id
            self.assertEqual(attendance.in_work_location_id, self.location)
