# -*- coding: utf-8 -*-
from odoo import models, fields, api


class odooloc(models.Model):
    _name = 'odooloc.odooloc'

    name = fields.Char(string="Title", required=True)
    description = fields.Text()


class MaintenanceEquipment(models.Model):
    _inherit = "maintenance.equipment"

    odooloc_reference_product_id = fields.Many2one('reference.product', string='Reference product')
