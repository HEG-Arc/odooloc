odoo.define('opensim.banner', function (require) {
    "use strict";
    var session = require('web.session');
    var Widget = require('web.Widget');
    var WebClient = require('web.AbstractWebClient');
    var bus = require('bus.bus').bus;

    var OpensimBanner = Widget.extend({
        template: 'opensim.js_banner',

        init: function (parent) {
            this._super.apply(this, arguments);
            this.active = true;
            // not necessary to add_channel here as it's added on python side by OpensimBusController
            //var channel = JSON.stringify([session.db, 'opensim.opensim', 'banner']);
            //bus.add_channel(channel);
        },
        willStart: function () {
            var self = this;
            var defered = this._rpc({
                model: 'opensim.opensim',
                method: 'banner_data'
            }).then(function (result) {
                self.active = result.active;
                self.team =  session.user_companies ? session.user_companies.current_company[1] : result.team;
                self.today = result.today;
                self.duration = result.duration;

            });
            return $.when(this._super.apply(this, arguments), defered);
        },
        start: function () {
            this._super.apply(this, arguments);
            bus.on("notification", this, this.on_notification);
            bus.start_polling(); //only necessary is longpolling not yet started by other module
        },
        destroy: function (animate) {
            if (this.refreshInterval) {
                clearInterval(this.refreshInterval);
                this.interval = null;
            }
            return this._super.apply(this, arguments);
        },
        on_notification: function (notifications) {
            // Old versions passes single notification item here. Convert it to the latest format.
            if (typeof notifications[0][0] === 'string') {
                notifications = [notifications]
            }
            var message,channel;
            for (var i = 0; i < notifications.length; i++) {
                channel = notifications[i][0];
                console.log('notif#',i, 'channel:',channel);
                console.log('msg:',notifications[i][1]);
                // we filter our message only
                if (channel[0]===session.db && channel[1]==='opensim.opensim' && channel[2]==='banner')
                    //and are only interrested in the last one
                    message = notifications[i][1];
            }
            if (message) {
                console.log('on_notification[' + channel + '] => ' + JSON.stringify(message));
                this.active = message.active;
                if (session.user_companies)
                //only user with multiple companies have current_company name in session
                    this.team = session.user_companies.current_company[1];
                this.tomorrow = message.today;
                this.duration = message.duration;
                this.renderElement();
                if (this.tomorrow != this.today) {
                    this.$el.addClass('os_blink');
                    var self = this;
                    this.$el.on('animationend webkitAnimationEnd oAnimationEnd MSAnimationEnd',
                        function () {
                            var items = self.$el.find('.item');
                            setTimeout(function () {
                                items.addClass('flipped');
                                items.on('webkitTransitionEnd otransitionend oTransitionEnd msTransitionEnd transitionend',
                                    function (e) {
                                        // update today on end of css animation
                                        // and re-render the widget (removing flipped case)
                                        self.today = self.tomorrow;
                                        self.renderElement();
                                    });
                            }, 200)
                        });
                }
            }
        },
    });
    // We create an instance of OpensimBanner  Widget directly from its module
    // we need a web_client instance as parent (for event handling / service support)
    var web_client = new WebClient();
    // here we wait for Session to have loaded qweb templates otherwise the widget rendering will fail (missing template)
    session.on('module_loaded', this, function () {
        var bannerWidget = new OpensimBanner(web_client);
        // add our banner after web_client top menu
        // wait for dom ready before seeking navbar
        require('web.dom_ready');
        var odoo_navbar = $('nav#oe_main_menu_navbar');
        bannerWidget.insertAfter(odoo_navbar);
    });

    return {OpensimBanner: OpensimBanner};
});
