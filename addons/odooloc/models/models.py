# -*- coding: utf-8 -*-
from odoo import models, fields, api


class odooloc(models.Model):
    _name = 'odooloc.rental'
    # _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Rental"
    _order = "name"
    name = fields.Char('Name', index=True, required=True, translate=True)
    sequence = fields.Integer('Sequence', default=1, help='Gives the sequence order when displaying a rental order list')
    customer_id = fields.Many2one('res.partner', 'Customer', required=True, domain="[('customer', '=', 'true')]")
    barcode_id = fields.Many2one('res.partner', 'Customer', domain="[('customer', '=', 'true')]")


class MaintenanceEquipment(models.Model):
    _inherit = "maintenance.equipment"

    odooloc_reference_product_id = fields.Many2one('stock.production.lot', string='Reference product', domain="[('name', '>', 0)]")
