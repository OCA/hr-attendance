/** @odoo-module **/
/* global Webcam */

import MyAttendances from "hr_attendance.my_attendances";
import Session from "web.session";

MyAttendances.include({
    events: _.extend({}, MyAttendances.prototype.events, {
        "click .o_hr_attendance_sign_in_out_icon": _.debounce(
            function () {
                if (this.has_group_webcam) {
                    $(".o_modal_camera_attendance").modal("show");
                } else {
                    this.update_attendance();
                }
            },
            200,
            true
        ),
        "click .o_hr_confirm_dialog_button": function () {
            this.update_attendance();
            $(".o_modal_camera_attendance").modal("hide");
        },
        "click .o_hr_cancel_dialog_button": function () {
            if (Webcam.live) Webcam.reset();
            $(".o_modal_camera_attendance").modal("hide");
        },
    }),

    init: function () {
        this._super.apply(this, arguments);
        this.image = null;
        this.has_group_webcam = false;
    },

    start: function () {
        this._super.apply(this, arguments);
        var self = this;
        this.getSession()
            .user_has_group("hr_attendance_webcam.group_hr_attendance_image_capture")
            .then((has_group) => {
                if (has_group) {
                    self.has_group_webcam = true;
                    Webcam.set({
                        width: 720,
                        height: 340,
                        image_format: "jpeg",
                        jpeg_quality: 90,
                        force_flash: false,
                        flip_horiz: false,
                        fps: 45,
                    });
                    this.modal = $(".o_modal_camera_attendance");
                    this.confirm_button = this.modal.find(
                        ".o_hr_confirm_dialog_button"
                    );
                    this.cancel_button = this.modal.find(".o_hr_cancel_dialog_button");

                    this.modal.on("hidden.bs.modal", function () {
                        Webcam.reset();
                        self.confirm_button.attr("disabled", "disabled");
                    });
                    this.modal.on("shown.bs.modal", function () {
                        Webcam.attach(".o_hr_attendance_webcam");
                        setTimeout(function () {
                            self.confirm_button.removeAttr("disabled");
                        }, 500);
                    });
                }
            });
    },

    update_attendance: function () {
        var self = this;
        if (Webcam.live) {
            Webcam.snap(function (data_uri) {
                self.image = data_uri.split(",")[1];
            });
            Webcam.reset();
        }
        const ctx = Object.assign(Session.user_context, {image: this.image});
        this._rpc({
            model: "hr.employee",
            method: "attendance_manual",
            args: [
                [self.employee.id],
                "hr_attendance.hr_attendance_action_my_attendances",
            ],
            context: ctx,
        }).then(function (result) {
            if (result.action) {
                self.do_action(result.action);
            } else if (result.warning) {
                self.displayNotification({title: result.warning, type: "danger"});
            }
        });
    },

    destroy: function () {
        if (Webcam.live) Webcam.reset();
        this._super.apply(this, arguments);
    },
});
