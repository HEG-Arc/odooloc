# -*- coding: utf-8 -*-
from odoo.tools import float_compare, DEFAULT_SERVER_DATETIME_FORMAT
from odoo import models, fields, api
from odoo.exceptions import UserError


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
        self._create_picking()

    @api.multi
    def _create_picking(self):
        self.env.cr.execute('SELECT id '
                            'FROM stock_picking_type where name=\'Pick\'')
        ptid = self.env.cr.fetchone()[0]

        stock_location = self.env.ref('stock.stock_location_stock')
        self.picking_ids = self.env['stock.picking'].create({
            'location_id': stock_location.id,
            'location_dest_id': stock_location.id,
            'picking_type_id': ptid,
            'move_type': self.picking_policy,
            'odooloc_id':self.id,
            'partner_id':self.partner_id.id,
            'origin':self.name,
        })

        for line in self.order_line:
            line._create_move(self.picking_ids.id)

class odoolocOrderLine(models.Model):
    _inherit = 'odooloc.order.line'


    move_ids = fields.One2many('stock.move', 'odooloc_line_id', string='Stock Moves')

    @api.multi
    def _create_move(self, p_pick_id):
        stock_location = self.env.ref('stock.stock_location_stock')
        move = self.env['stock.move'].create({
            'name': 'Use on MyLocation',
            'location_id': stock_location.id,
            'location_dest_id': stock_location.id,
            'product_id': self.product_id.id,
            'product_uom': self.product_uom.id,
            'product_uom_qty': self.product_uom_qty,
            'odooloc_line_id': self.id,
            'picking_id': p_pick_id,
        })
        move._action_confirm()
        self.move_ids._action_assign()
        # This creates a stock.move.line record.
        # You could also do it manually using self.env['stock.move.line'].create({...})
        #move_ids.move_line_ids.write({'qty_done': line.product_uom_qty})
        self.move_ids._action_done()

        #self.order_id._create_picking()