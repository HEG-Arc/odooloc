# -*- coding: utf-8 -*-
from odoo import http, fields

class Opensim(http.Controller):
    @http.route('/opensim/opensim/', auth='public')
    def index(self, **kw):
        return "OdooSIM time is :{}".format(fields.Datetime.now())

#     @http.route('/opensim/opensim/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('opensim.listing', {
#             'root': '/opensim/opensim',
#             'objects': http.request.env['opensim.opensim'].search([]),
#         })

#     @http.route('/opensim/opensim/objects/<model("opensim.opensim"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('opensim.object', {
#             'object': obj
#         })
