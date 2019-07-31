# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from odoo import models, fields, api


class odooloc(models.Model):
    _name = 'odooloc.order'
    # _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Rental order"
    _order = 'name desc'

    name = fields.Char('Rental Reference', required=True, index=True, copy=False, default='New')
    sequence = fields.Integer('Sequence', default=1,
                              help='Gives the sequence order when displaying a rental order list')
    customer_id = fields.Many2one('res.partner', 'Customer', required=True, domain="[('customer', '=', 'true')]")
    barcode_id = fields.Many2one('res.partner', 'Customer', domain="[('customer', '=', 'true')]")
    date_start = fields.Datetime('Start date', required=True, index=True, copy=False, default=fields.Datetime.now)
    date_end = fields.Datetime('End date', required=True, index=True, copy=False, default=fields.Datetime.now)
    date_out = fields.Datetime('Picking OUT date', required=True, index=True, copy=False, default=fields.Datetime.now)
    date_in = fields.Datetime('Picking IN date', required=True, index=True, copy=False, default=fields.Datetime.now)
    event_name = fields.Char('Event name')
    event_adress = fields.Char('Event adress')
    event_zip = fields.Char('Event ZIP')
    event_city = fields.Char('Event city')
    comment = fields.Char('Comments')
    pick_method = fields.Selection([
        ('company', 'Delivered by company'),
        ('self', 'Self-service')
    ], required=True, index=True, copy=False, default='self')
    assembly_method = fields.Selection([
        ('company', 'Assembly by company'),
        ('self', 'Assembly by customer')
    ], required=True, index=True, copy=False, default='self')

    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirmed'),
        ('cancel', 'Canceled')
    ], string='Status', readonly=True, index=True, copy=False, default='draft', track_visibility='onchange')

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('odooloc.order') or '/'
        return super(odooloc, self).create(vals)

    @api.multi
    def action_confirm_order(self):
        self.write({'state': 'confirm'})
        return True

    @api.multi
    def action_cancel_order(self):
        return self.write({'state': 'cancel'})


class odooloc(models.Model):
    _name = 'odooloc.order.line'
    # _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Rental order line"
    _order = 'order_id desc, name desc'

    order_id = fields.Many2one('odooloc.rental', 'id', required=True, ondelete='cascade')
    name = fields.Char('Rental Order Line Reference', required=True, index=True, copy=False, default='New')
    sequence = fields.Integer(string='Sequence', default=10)



class MaintenanceEquipment(models.Model):
    _inherit = "maintenance.equipment"

    odooloc_reference_product_id = fields.Many2one('stock.production.lot', string='Reference product',
                                                   domain="[('name', '>', 0)]")
