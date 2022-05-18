odoo.define("hr_birhday_welcome_message.greeting_message_birthday_message", function(
    require
) {
    "use strict";

    var core = require("web.core");
    var greeting_message = require("hr_attendance.greeting_message");
    var _t = core._t;

    greeting_message.include({
        init: function(parent, action) {
            this._super.apply(this, arguments);
            this.is_birthday = action.is_birthday;
        },

        _get_birthday_message: function() {
            return _t(
                "Happy Birthday! <i class='fa fa-birthday-cake' /> <br/> Enjoy your day"
            );
        },
        welcome_message: function() {
            this._super.apply(this, arguments);
            if (this.is_birthday) {
                this.$(".o_hr_attendance_random_message").html(
                    this._get_birthday_message()
                );
            }
        },
    });
});
