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

    picking_ids = fields.One2many('stock.picking', 'odooloc_id', string='Pickings')




class odoolocOrderLine(models.Model):
    _inherit = 'odooloc.order.line'

    move_ids = fields.One2many('stock.move', 'odooloc_line_id', string='Stock Moves')

    @api.multi
    def _action_launch_procurement_rule(self):
        for line in self:
            values = line._prepare_procurement_values(group_id=group_id)
            
            self.env['procurement.group'].run(line.product_id, line.product_uom_qty, line.product_uom,
                                              line.order_id.partner_id.property_stock_customer, line.name,
                                              line.order_id.name, values)