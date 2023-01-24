/* global GelocationPositionError */
/* Copyright 2023 Alexandre D. Díaz - Grupo Isonor
 * License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl). */
odoo.define("hr_attendance_geolocation.geolocation_service", function (require) {
    "use strict";

    const core = require("web.core");
    const AbstractService = require("web.AbstractService");
    const session = require("web.session");

    const GeolocationService = AbstractService.extend({
        dependencies: [],

        start: function () {
            this._hasGeolocation = typeof navigator.geolocation !== "undefined";
        },

        updateUserContextAsync: function (options) {
            return new Promise((resolve, reject) => {
                this.updateUserContext(resolve, reject, options);
            });
        },

        updateUserContext: function (onSuccess, onError, options) {
            this.getLocation(
                (position) => {
                    session.user_geolocation_context = {
                        latitude: position.coords.latitude,
                        longitude: position.coords.longitude,
                    };
                    if (typeof onSuccess !== "undefined") {
                        onSuccess(position);
                    }
                },
                (err) => {
                    console.warn(`HR Attendance Geolocation Error: ${err.message}`);
                    session.user_geolocation_context = {
                        latitude: 0,
                        longitude: 0,
                    };
                    if (typeof onError !== "undefined") {
                        onError(err);
                    }
                },
                options
            );
        },

        getLocation: function (onSuccess, onError, options) {
            if (!this._hasGeolocation) {
                return onError(
                    new GelocationPositionError("Service geolocation not available")
                );
            }
            if (_.isEmpty(options)) {
                options = {
                    enableHighAccuracy: true,
                    timeout: 5000,
                    maximumAge: 60000,
                };
            }
            navigator.geolocation.getCurrentPosition(onSuccess, onError, options);
        },
    });

    core.serviceRegistry.add("hr_attendance_geolocation_service", GeolocationService);
    return GeolocationService;
});
