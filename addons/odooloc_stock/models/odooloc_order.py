# -*- coding: utf-8 -*-

from odoo import models, fields, api


class odoolocOrder(models.Model):
    _inherit = "odooloc.order"

    @api.model
    def _default_warehouse_id(self):
        company = self.env.user.company_id.id
        warehouse_ids = self.env['stock.warehouse'].search([('company_id', '=', company)], limit=1)
        return warehouse_ids

    picking_policy = fields.Selection([
        ('direct', 'Deliver each product when available'),
        ('one', 'Deliver all products at once')],
        string='Shipping Policy', required=True, readonly=True, default='one',
        states={'draft': [('readonly', False)], 'rent': [('readonly', False)]})
    warehouse_id = fields.Many2one(
        'stock.warehouse', string='Warehouse',
        required=True, readonly=True, states={'draft': [('readonly', False)], 'rent': [('readonly', False)]},
        default=_default_warehouse_id)

    location_src = field

    picking_ids = fields.One2many('stock.picking', 'odooloc_id', string='Pickings')




class odoolocOrderLine(models.Model):
    _inherit = 'odooloc.order.line'

