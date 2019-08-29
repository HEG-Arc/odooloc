# -*- coding: utf-8 -*-

from odoo import models, fields, api


class odoolocOrder(models.Model):
    _inherit = "odooloc.order"

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

