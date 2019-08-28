# -*- coding: utf-8 -*-
from odoo import models, fields

from odoo.addons import decimal_precision as dp

# Adding product rental price for rentable products
class ProductTemplate(models.Model):
    _inherit = "product.template"
    rental_price = fields.Float('Unit price per day', digits=dp.get_precision('Rental Price'),
                                     domain=[('rental', '=', True)])
