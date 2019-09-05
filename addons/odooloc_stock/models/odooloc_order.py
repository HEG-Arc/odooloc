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
        string='Shipping Policy', required=True, readonly=True, default='direct',
        states={'draft': [('readonly', False)], 'sent': [('readonly', False)]})

    warehouse_id = fields.Many2one(
        'stock.warehouse', string='Warehouse',
        required=True, readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},
        default=_default_warehouse_id)

    picking_state = fields.Selection([
        ('none', 'No picking status'),
        ('picking', 'Preparing items'),
        ('picked', 'Items Ready'),
        ('handed', 'Handed to Customer'),
        ('back', 'Back to Company'),
        ('end', 'Items back in stock')
    ], string='Picking Status', readonly=True, copy=False, index=True, track_visibility='onchange', default='none')

    picking_ids = fields.One2many('stock.picking', 'odooloc_id', string='Pickings')

    delivery_count = fields.Integer(string='Delivery Orders', compute='_compute_picking_ids')

    procurement_group_id = fields.Many2one('procurement.group', 'Procurement Group', copy=False)

    @api.multi
    def _odooloc_confirm_order(self):
        super(odoolocOrder, self)._odooloc_confirm_order()
        for order in self:
            order.order_line._action_launch_procurement_rule()

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


class odoolocOrderLine(models.Model):
    _inherit = 'odooloc.order.line'

    route_id = fields.Many2one('stock.location.route', string='Route', domain=[('odooloc_selectable', '=', True)],
                               ondelete='restrict')
    move_ids = fields.One2many('stock.move', 'odooloc_line_id', string='Stock Moves')

    @api.model
    def create(self, values):
        line = super(odoolocOrderLine, self).create(values)
        if line.state == 'rent':
            line._action_launch_procurement_rule()
        return line

    @api.multi
    def write(self, values):
        lines = self.env['odooloc.order.line']
        if 'product_uom_qty' in values:
            precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
            lines = self.filtered(
                lambda r: r.state == 'rent' and float_compare(r.product_uom_qty, values['product_uom_qty'],
                                                              precision_digits=precision) == -1)
        previous_product_uom_qty = {line.id: line.product_uom_qty for line in lines}
        res = super(odoolocOrderLine, self).write(values)
        if lines:
            lines.with_context(previous_product_uom_qty=previous_product_uom_qty)._action_launch_procurement_rule()
        return res

    @api.multi
    def _prepare_procurement_values(self, group_id=False):
        """ Prepare specific key for moves or other components that will be created from a procurement rule
        comming from a sale order line. This method could be override in order to add other custom key that could
        be used in move/po creation.
        """
        values = super(odoolocOrderLine, self)._prepare_procurement_values(group_id)
        self.ensure_one()

        values.update({
            'company_id': self.order_id.company_id,
            'group_id': group_id,
            'odooloc_line_id': self.id,
            'route_ids': self.route_id,
            'warehouse_id': self.order_id.warehouse_id or False,
            'partner_id': self.order_id.partner_id
        })
        return values

    def _get_qty_procurement(self):
        self.ensure_one()
        qty = 0.0
        for move in self.move_ids.filtered(lambda r: r.state != 'cancel'):
            if move.picking_code == 'outgoing':
                qty += move.product_uom._compute_quantity(move.product_uom_qty, self.product_uom,
                                                          rounding_method='HALF-UP')
            elif move.picking_code == 'incoming':
                qty -= move.product_uom._compute_quantity(move.product_uom_qty, self.product_uom,
                                                          rounding_method='HALF-UP')
        return qty

    @api.multi
    def _action_launch_procurement_rule(self):
        """
        Launch procurement group run method with required/custom fields generated by a
        rental order line. procurement group will launch '_run_move', '_run_buy' or '_run_manufacture'
        depending on the rental order line product rule.
        """
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        errors = []
        for line in self:
            if line.state != 'rent' or not line.product_id.type in ('consu', 'product'):
                continue
            qty = line._get_qty_procurement()
            if float_compare(qty, line.product_uom_qty, precision_digits=precision) >= 0:
                continue

            group_id = line.order_id.procurement_group_id
            if not group_id:
                group_id = self.env['procurement.group'].create({
                    'name': line.order_id.name, 'move_type': line.order_id.picking_policy,
                    'odooloc_id': line.order_id.id,
                    'partner_id': line.order_id.partner_id.id,
                })
                line.order_id.procurement_group_id = group_id
            else:
                # In case the procurement group is already created and the order was
                # cancelled, we need to update certain values of the group.
                updated_vals = {}
                if group_id.partner_id != line.order_id.partner_id:
                    updated_vals.update({'partner_id': line.order_id.partner_shipping_id.id})
                if group_id.move_type != line.order_id.picking_policy:
                    updated_vals.update({'move_type': line.order_id.picking_policy})
                if updated_vals:
                    group_id.write(updated_vals)

            values = line._prepare_procurement_values(group_id=group_id)
            product_qty = line.product_uom_qty #- qty

            procurement_uom = line.product_uom
            #quant_uom = line.product_id.uom_id
            #get_param = self.env['ir.config_parameter'].sudo().get_param
            #if procurement_uom.id != quant_uom.id and get_param('stock.propagate_uom') != '1':
                #product_qty = line.product_uom._compute_quantity(product_qty, quant_uom, rounding_method='HALF-UP')
                #procurement_uom = quant_uom

            try:
                self.env['procurement.group'].run(line.product_id, product_qty, procurement_uom,
                                                  line.order_id.partner_id.property_stock_customer, line.name,
                                                  line.order_id.name, values)
            except UserError as error:
                errors.append(error.name)
        if errors:
            raise UserError('\n'.join(errors))
        return True