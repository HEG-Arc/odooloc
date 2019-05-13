# -*- coding: utf-8 -*-

from odoo.addons.bus.controllers.main import BusController
from odoo.http import request


class OpensimBusController(BusController):

    # --------------------------
    # Extends BUS Controller Poll to add our own channel
    # --------------------------
    def _poll(self, dbname, channels, last, options):
        if request.session.uid:
            channels = list(channels)  # do not alter original list
            # we create a single 'banner' "broadcast" channel for all loggedin users so we ignore session uid information
            channels.append((request.db, 'opensim.opensim', 'banner')) # request.session.uid))
        return super(OpensimBusController, self)._poll(dbname, channels, last, options)
