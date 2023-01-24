/* Copyright ForgeFlow - Adria Gil Sorribes
   Copyright Tecnativa - David Vidal
   Copyright Grupo Isonor - Alexandre D. Díaz
   License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
*/
odoo.define("hr_attendance_geolocation.attendances_geolocation", function (require) {
    "use strict";

    const MyAttendances = require("hr_attendance.my_attendances");
    const KioskConfirm = require("hr_attendance.kiosk_confirm");

    // After every check in or check out is made, the widget is reloaded, so we can
    // rely on the init hook to load the users location. When the next check in or check
    // is made, the location will be injected in the context so we can catch it in
    // the server code.
    MyAttendances.include({
        willStart: function () {
            const prom = this.call(
                "hr_attendance_geolocation_service",
                "updateUserContextAsync"
            );
            return Promise.all([prom, this._super.apply(this, arguments)]);
        },
    });

    // With Kiosk, we had no method to override, as the event property that triggers the
    // update is mapped directly to a function on the fly. In this case, we'll use the
    // asyncronous willStart method so we can wait for the location to be resolved.
    KioskConfirm.include({
        willStart: function () {
            const prom = this.call(
                "hr_attendance_geolocation_service",
                "updateUserContextAsync"
            );
            return Promise.all([prom, this._super.apply(this, arguments)]);
        },
    });
});
