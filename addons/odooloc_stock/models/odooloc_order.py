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


    @api.multi
    def odooloc_confirm_order(self):
        super(odoolocOrder, self).odooloc_confirm_order()
        for order in self:
            order.order_line._create_move()

    @api.multi
    def _create_picking(self):
        stock_location = self.env.ref('stock.stock_location_stock')
        self.picking_ids = self.env['stock.picking'].create({
            'location_id': stock_location.id,
            'location_dest_id': stock_location.id,
            'picking_type_id': 4,
            'move_type': self.picking_policy,
        })

        for line in self.order_line:
            line.move_ids.picking_id =  self.picking_ids

class odoolocOrderLine(models.Model):
    _inherit = 'odooloc.order.line'

    move_ids = fields.One2many('stock.move', 'odooloc_line_id', string='Stock Moves')

    @api.multi
    def _create_move(self):
        stock_location = self.env.ref('stock.stock_location_stock')
        for line in self:
            self.move_ids = self.env['stock.move'].create({
                'name': 'Items preparation for a rent',
                'location_id': stock_location.id,
                'location_dest_id': stock_location.id,
                'product_id': line.product_id.id,
                'product_uom': line.product_uom.id,
                'product_uom_qty': line.product_uom_qty,
                #'picking_id': self.order_id.
            })
            self.move_ids._action_confirm()
            self.move_ids._action_assign()
            # This creates a stock.move.line record.
            # You could also do it manually using self.env['stock.move.line'].create({...})
            #move_ids.move_line_ids.write({'qty_done': line.product_uom_qty})
            self.move_ids._action_done()

        self.order_id._create_picking()

