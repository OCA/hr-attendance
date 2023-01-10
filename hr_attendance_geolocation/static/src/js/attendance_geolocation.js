/* Copyright ForgeFlow - Adria Gil Sorribes
   Copyright Tecnativa - David Vidal
   License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
*/
odoo.define("hr_attendance_geolocation.attendances_geolocation", function(require) {
    "use strict";

    const session = require("web.session");

    var MyAttendances = require("hr_attendance.my_attendances");
    var KioskConfirm = require("hr_attendance.kiosk_confirm");

    const locationOptions = {
        enableHighAccuracy: true,
        timeout: 5000,
        maximumAge: 60000,
    };

    // After every check in or check out is made, the widget is reloaded, so we can
    // rely on the init hook to load the users location. When the next check in or check
    // is made, the location will be injected in the context so we can catch it in
    // the server code.
    MyAttendances.include({
        /**
         * @override
         */
        init: function() {
            this._super.apply(this, arguments);
            this.position = {coords: {latitude: 0.0, longitude: 0.0}};
            if (navigator.geolocation) {
                navigator.geolocation.getCurrentPosition(
                    position => {
                        this.position = position;
                    },
                    error => {
                        console.warn(`ERROR ${error.code}: ${error.message}`);
                    },
                    locationOptions
                );
            }
        },
        /**
         * @override
         */
        update_attendance: function() {
            Object.assign(session.user_context, {
                attendance_location: [
                    this.position.coords.latitude,
                    this.position.coords.longitude,
                ],
            });
            return this._super(...arguments);
        },
    });

    // With Kiosk, we had no method to override, as the event property that triggers the
    // update is mapped directly to a function on the fly. In this case, we'll use the
    // asyncronous willStart method so we can wait for the location to be resolved.
    KioskConfirm.include({
        /**
         * @override
         */
        init: function() {
            this.position = {coords: {latitude: 0.0, longitude: 0.0}};
            this._super.apply(this, arguments);
        },
        /**
         * @override
         *
         * @returns {Promise}
         */
        willStart: async function() {
            await this._super(...arguments);
            if (navigator.geolocation) {
                try {
                    this.position = await this.getCoordinates();
                } catch (error) {
                    console.warn(`ERROR ${error.code}: ${error.message}`);
                }
            }
        },
        /**
         * @override
         */
        start: function() {
            Object.assign(session.user_context, {
                attendance_location: [
                    this.position.coords.latitude,
                    this.position.coords.longitude,
                ],
            });
            return this._super(...arguments);
        },
        /**
         * We need to Promisify the getCurrentPosition method to be able to await for
         * its resolution.
         *
         * @returns {Promise}
         */
        getCoordinates: function() {
            return new Promise((resolve, reject) => {
                navigator.geolocation.getCurrentPosition(
                    resolve,
                    reject,
                    locationOptions
                );
            });
        },
    });
});
