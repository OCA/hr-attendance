/** @odoo-module **/
/* Copyright 2023 Alexandre D. Díaz - Grupo Isonor
 * License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl). */

import {registry} from "@web/core/registry";
import * as legacySession from "web.session";

const LegacyGelocationSessionUserContextService = {
    dependencies: ["user"],

    start(env) {
        Object.defineProperty(legacySession, "user_geolocation_context", {
            set: (values) => {
                const {latitude, longitude} = values;
                if (
                    typeof latitude !== "undefined" &&
                    typeof longitude !== "undefined"
                ) {
                    env.services.user.updateContext({
                        latitude: latitude,
                        longitude: longitude,
                    });
                }
            },
        });
    },
};

registry
    .category("services")
    .add(
        "legacy_geolocation_session_user_context",
        LegacyGelocationSessionUserContextService
    );
