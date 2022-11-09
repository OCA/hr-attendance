odoo.define("hr_attendance_overtime.my_attendances", function (require) {
    "use strict";

    var time = require("web.time");
    var MyAttendances = require("hr_attendance.my_attendances");
    MyAttendances.include({
        willStart: function () {
            var self = this;
            this.format_time = time.getLangTimeFormat();
            var def = this._rpc({
                model: "hr.employee",
                method: "todays_working_times",
                args: [[["user_id", "=", this.getSession().uid]]],
            }).then(function (res) {
                self.overtime_info = res;
            });

            return Promise.all([def, this._super.apply(this, arguments)]);
        },
        timeToStr: function (utc_str_datetime, force_time_format) {
            const time_format = force_time_format
                ? time.strftime_to_moment_format(force_time_format)
                : this.format_time;
            return moment.utc(utc_str_datetime).local().format(time_format);
        },
        progressBarStyle: function (hours) {
            return `width: ${(hours / 24) * 100}%; font-size: 1.1em;`;
        },
        progressBarTheoreticalClass: function (worktime) {
            const baseClass = "progress-bar ";
            if (worktime.is_worktime === true) {
                return baseClass + "bg-primary";
            }
            return baseClass + "bg-light";
        },
        progressBarWorkedTimeTitle: function (worktime, force_time_format) {
            let title = "";
            if (worktime.is_worktime === true) {
                title = `${this.timeToStr(
                    worktime.start,
                    force_time_format
                )}-${this.timeToStr(worktime.end, force_time_format)}`;
            }
            return title;
        },
        progressBarWorkedTimeClass: function (worktime) {
            const baseClass = "progress-bar progress-bar-striped ";
            if (worktime.is_worktime === true) {
                return (
                    baseClass + (worktime.is_checked_out ? "bg-success" : "bg-warning")
                );
            }
            return baseClass + "bg-light";
        },
        signOutExtraClass() {
            let btn_style = "btn-danger";
            const btn_styles = {
                "CHECK-OUT-ONTIME": "btn-info",
                "CHECK-OUT-EARLIER": "btn-danger",
                "CHECK-OUT-LATE": "btn-warning",
                "CHECK-OUT-NO-PREVIOUS": "btn-warning",
            };
            if (this.overtime_info.state in btn_styles) {
                btn_style = btn_styles[this.overtime_info.state];
            }
            return btn_style;
        },
        signInExtraClass() {
            let btn_style = "btn-danger";
            const btn_styles = {
                "CHECK-IN-ONTIME": "btn-success",
                "CHECK-IN-EARLIER": "btn-primary",
                "CHECK-IN-LATE": "btn-danger",
                "CHECK-IN-NO-NEXT": "btn-primary",
            };
            if (this.overtime_info.state in btn_styles) {
                btn_style = btn_styles[this.overtime_info.state];
            }
            return btn_style;
        },
    });
});
