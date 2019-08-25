from odoo import models, fields

class StockLocationRoute(models.Model):
    _inherit = "stock.location.route"
    odooloc_selectable = fields.Boolean("Selectable on Rental Order Line")

class StockMove(models.Model):
    _inherit = "stock.move"
    odooloc_line_id = fields.Many2one('odooloc.order.line', 'Rental Line')

class ProcurementGroup(models.Model):
    _inherit = 'procurement.group'
    odooloc_id = fields.Many2one('odooloc.order', 'Rental Order')

class StockPicking(models.Model):
    _inherit = "stock.picking"
    odooloc_id = fields.Many2one(related="group_id.odooloc_id", string="Rental Order", store=True)