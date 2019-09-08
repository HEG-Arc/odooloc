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
    delivery_count = fields.Integer(string='Delivery Orders', compute='_compute_picking_ids')

    @api.depends('picking_ids')
    def _compute_picking_ids(self):
        for order in self:
            order.delivery_count = len(order.picking_ids)

    @api.multi
    def action_view_delivery(self):
        '''
        This function returns an action that display existing delivery orders
        of given sales order ids. It can either be a in a list or in a form
        view, if there is only one delivery order to show.
        '''
        action = self.env.ref('stock.action_picking_tree_all').read()[0]

        pickings = self.mapped('picking_ids')
        if len(pickings) > 1:
            action['domain'] = [('id', 'in', pickings.ids)]
        elif pickings:
            action['views'] = [(self.env.ref('stock.view_picking_form').id, 'form')]
            action['res_id'] = pickings.id
        return action

    @api.multi
    def odooloc_confirm_order(self):
        super(odoolocOrder, self).odooloc_confirm_order()
        self._create_picking()

    @api.multi
    def _default_picking_type(self):
        picking_type_name = 'Rental Picking'

        self.env.cr.execute('SELECT id '
                            'FROM stock_picking_type where name=\''+picking_type_name+'\'')
        picking_id = self.env.cr.fetchone()[0]

        default_picking_type = self.env['stock.picking.type'].search([('id','=',picking_id)])

        # picking_type_name = 'Rental Picking'
        #         default_picking_type = self.env['stock.picking.type'].search([('name', 'in', picking_type_name)])

        # if not default_picking_type:
        #     default_picking_type = self.env.ref('stock.stock_picking_type').create({
        #
        #     })

        return default_picking_type

    @api.multi
    def _create_picking(self):
        stock_location = self.env.ref('stock.stock_location_stock')
        self.picking_ids = self.env['stock.picking'].create({
            'location_id': self._default_picking_type().default_location_src_id.id,
            'location_dest_id': self._default_picking_type().default_location_dest_id.id,
            'picking_type_id': self._default_picking_type().id,
            'move_type': self.picking_policy,
            'odooloc_id': self.id,
            'partner_id': self.partner_id.id,
            'origin': self.name,
        })

        for line in self.order_line:
            line._create_move(self.picking_ids.id)


class odoolocOrderLine(models.Model):
    _inherit = 'odooloc.order.line'

    # # Add relation to routes model
    # route_id = fields.Many2one('stock.location.route', string='Route', domain=[('odooloc_selectable', '=', True)],
    #     ondelete='restrict')

    move_ids = fields.One2many('stock.move', 'odooloc_line_id', string='Stock Moves')

    @api.multi
    def _create_move(self, p_pick_id):
        stock_location = self.env.ref('stock.stock_location_stock')
        move = self.env['stock.move'].create({
            'name': 'Use on MyLocation',
            'location_id': stock_location.id,
            'location_dest_id': p_pick_id,
            'product_id': self.product_id.id,
            'product_uom': self.product_uom.id,
            'product_uom_qty': self.product_uom_qty,
            'odooloc_line_id': self.id,
            'picking_id': p_pick_id,
        })
        move._action_confirm()
        self.move_ids._action_assign()
        self.move_ids._action_done()
