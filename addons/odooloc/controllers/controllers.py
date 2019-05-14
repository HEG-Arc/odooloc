# -*- coding: utf-8 -*-
from odoo import http


class Odooloc(http.Controller):
    @http.route('/odooloc/odooloc/', auth='public')
    def index(self, **kw):
        return "Welcome to Odooloc"

    @http.route('/odooloc/odooloc/objects/', auth='public')

    def list(self, **kw):
        return http.request.render('odooloc.listing', {
            'root': '/odooloc/odooloc',
            'objects': http.request.env['odooloc.odooloc'].search([]),
        })

#     @http.route('/odooloc/odooloc/objects/<model("odooloc.odooloc"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('odooloc.object', {
#             'object': obj
#         })