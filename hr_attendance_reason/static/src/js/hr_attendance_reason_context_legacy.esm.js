/** @odoo-module **/

import {registry} from "@web/core/registry";
import * as legacySession from "web.session";

const LegacyHrAttendanceReasonSessionUserContextService = {
    dependencies: ["user"],

    start(env) {
        Object.defineProperty(legacySession, "user_hr_attendance_reason_context", {
            set: (values) => {
                for (var key in values) {
                    env.services.user.updateContext({key: values[key]});
                }
            },
        });
    },
};

registry
    .category("services")
    .add(
        "legacy_hr_attendance_reason_session_user_context",
        LegacyHrAttendanceReasonSessionUserContextService
    );
