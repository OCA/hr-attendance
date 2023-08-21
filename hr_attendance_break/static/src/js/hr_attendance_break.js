/* Copyright 2023 Hunki Enterprises BV
 * License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl). */

odoo.define("hr_attendance_break", function (require) {
    "use strict";

    var myAttendances = require("hr_attendance.my_attendances");
    var field_utils = require("web.field_utils");

    myAttendances.include({
        events: _.extend({}, myAttendances.prototype.events, {
            "click .o_hr_attendance_break_icon": _.debounce(
                function () {
                    this._hr_attendance_break();
                },
                200,
                true
            ),
        }),

        willStart: function () {
            var self = this;
            var promise = this._rpc({
                model: "hr.employee",
                method: "search_read",
                args: [
                    [["user_id", "=", this.getSession().uid]],
                    ["break_state", "break_hours_today"],
                ],
            }).then(function (data) {
                self.break_state = data[0].break_state;
                self.break_hours_today = field_utils.format.float_time(
                    data[0].break_hours_today
                );
            });
            return Promise.all([this._super.apply(this, arguments), promise]);
        },

        _hr_attendance_break: function () {
            var self = this;
            return this._rpc({
                model: "hr.employee",
                method: "attendance_manual_break",
                args: [
                    [this.employee.id],
                    "hr_attendance.hr_attendance_action_my_attendances",
                ],
            }).then(function () {
                return self.do_action(
                    "hr_attendance.hr_attendance_action_my_attendances"
                );
            });
        },
    });
});
