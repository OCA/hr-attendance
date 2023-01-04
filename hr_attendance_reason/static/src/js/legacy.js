odoo.define("hr_attendance_reason.hr_attendance_reason_service", function (require) {
    "use strict";
    const session = require("web.session");
    var core = require("web.core");
    const AbstractService = require("web.AbstractService");

    const HrAttendanceReasonService = AbstractService.extend({
        dependencies: [],
        updateUserContextAsync: function (options) {
            return new Promise(() => {
                this.updateUserContext(options);
            });
        },
        updateUserContext: function (options) {
            session.user_hr_attendance_reason_context = options;
        },
    });

    core.serviceRegistry.add("hr_attendance_reason_service", HrAttendanceReasonService);
    return HrAttendanceReasonService;
});
