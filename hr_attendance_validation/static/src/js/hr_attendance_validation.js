odoo.define("hr_attendance_validation.my_attendances", function (require) {
    "use strict";

    var MyAttendances = require("hr_attendance.my_attendances");
    var field_utils = require("web.field_utils");

    MyAttendances.include({
        willStart: function () {
            var self = this;
            self.hours_current_week = 0;
            // PV: we could avoid extra request if hr_attendance allowed to defined which fields
            // to requests
            var def = this._rpc({
                model: "hr.employee",
                method: "search_read",
                args: [
                    [["user_id", "=", this.getSession().uid]],
                    ["hours_current_week"],
                ],
            }).then(function (res) {
                if (res.length) {
                    self.hours_current_week = field_utils.format.float_time(
                        res[0].hours_current_week
                    );
                }
            });

            return Promise.all([def, this._super.apply(this, arguments)]);
        },
    });
});
