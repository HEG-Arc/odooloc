odoo.define('opensim.simulation_time', function (require) {
    "use strict";
    var session = require('web.session');
    var datepicker = require('web.datepicker');
    var basic_fields = require('web.basic_fields');



    var __makeDatePicker= basic_fields.FieldDateTime.prototype._makeDatePicker;
    basic_fields.FieldDateTime.prototype._makeDatePicker = function()
    {
       /* if (!this.value)
            this.value = new moment(); //.add(10,'days');
        else
            this.value.add(10,'days');*/
        return __makeDatePicker.apply(this);
        /*
            var value = this.value && this.value.clone().add(this.getSession().getTZOffset(this.value), 'minutes');
            return new datepicker.DateTimeWidget(this, {defaultDate: value});
         */
    };
    var __start = datepicker.DateTimeWidget.prototype.start;
     datepicker.DateTimeWidget.prototype.start = function() {
        /* if (!this.options.defaultDate)
            this.options.defaultDate = new moment().add(5,'days');
         else
             this.options.defaultDate.add(5,'days');*/
         __start.apply(this);
     };

    /*    this.$input = this.$('input.o_datepicker_input');
        this.$input.focus(function(e) {
            e.stopImmediatePropagation();
        });
        if (!this.options.defaultDate)
            this.options.defaultDate = new moment().add(5,'days');
        this.$input.datetimepicker(this.options);
        this.picker = this.$input.data('DateTimePicker');
        this.$input.click(this.picker.toggle.bind(this.picker));
        this._setReadonly(false);
    };*/

/*    datepicker.DateTimeWidget.prototype.changeDatetime = function() {
        if (this.isValid()) {
            var oldValue = this.getValue();
            if (oldValue) //make it possibly same as new value
                oldValue.add(5,'days');

            var uiValue = this.$input.val() || false;
            this.setValue(this._parseClient(uiValue).add(5,'day'));
            //this._setValueFromUi();
            var newValue = this.getValue();
            var hasChanged = !oldValue !== !newValue;
            hasChanged = hasChanged && !oldValue;
            if (oldValue && newValue) {
                var formattedOldValue = oldValue.format(time.getLangDatetimeFormat());
                var formattedNewValue = newValue.format(time.getLangDatetimeFormat())
                if (formattedNewValue !== formattedOldValue) {
                    hasChanged = true;
                }
            }
            if (hasChanged) {
                // The condition is strangely written; this is because the
                // values can be false/undefined
                this.trigger("datetime_changed");
            }
        }
    }*/;

    var simulationtime_now = function()
    {
        //return new Moment();
        return new Date();
    };
    return  {
        simulationtime_now: simulationtime_now,
    };
});
