# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from odoo import models, fields, api


class odooloc(models.Model):
    _name = 'odooloc.rental'
    # _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Rental"
    _order = "name"

    name = fields.Char('Rental Reference', required=True, index=True, copy=False, default='New')
    sequence = fields.Integer('Sequence', default=1,
                              help='Gives the sequence order when displaying a rental order list')
    customer_id = fields.Many2one('res.partner', 'Customer', required=True, domain="[('customer', '=', 'true')]")
    barcode_id = fields.Many2one('res.partner', 'Customer', domain="[('customer', '=', 'true')]")
    date_begin = fields.Datetime('Beginning date', required=True, index=True, copy=False, default=fields.Datetime.now)
    date_end = fields.Datetime('Ending date', required=True, index=True, copy=False, default=fields.Datetime.now)

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('odooloc.rental') or '/'
        return super(odooloc, self).create(vals)


class MaintenanceEquipment(models.Model):
    _inherit = "maintenance.equipment"

    odooloc_reference_product_id = fields.Many2one('stock.production.lot', string='Reference product',
                                                   domain="[('name', '>', 0)]")
