# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from odoo.addons import decimal_precision as dp
from odoo import models, fields, api


class odoolocOrder(models.Model):
    _name = 'odooloc.order'
    # _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Rental order"
    _order = 'name desc'

    @api.depends('order_line.price_total')
    def _amount_all(self):
        for order in self:
            amount_untaxed = amount_tax = 0.0
            for line in order.order_line:
                amount_untaxed += line.price_subtotal
                amount_tax += line.price_tax
            order.update({
                'amount_untaxed': order.currency_id.round(amount_untaxed),
                'amount_tax': order.currency_id.round(amount_tax),
                'amount_total': amount_untaxed + amount_tax,
            })

    READONLY_STATES = {
        'confirm': [('readonly', True)],
        'cancel': [('readonly', True)],
    }

    amount_untaxed = fields.Monetary(string='Untaxed Amount', store=True, readonly=True, compute='_amount_all',
                                     track_visibility='always')
    amount_tax = fields.Monetary(string='Taxes', store=True, readonly=True, compute='_amount_all')
    amount_total = fields.Monetary(string='Total', store=True, readonly=True, compute='_amount_all')

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
        ('draft', 'Waiting confirmation'),
        ('confirm', 'Confirmed'),
        ('cancel', 'Canceled')
    ], string='Status', readonly=True, index=True, copy=False, default='draft', track_visibility='onchange')

    customer_id = fields.Many2one('res.partner', string='Vendor', required=True, states=READONLY_STATES,
                                 change_default=True, track_visibility='always')

    currency_id = fields.Many2one('res.currency', 'Currency', required=True, states=READONLY_STATES, \
                                  default=lambda self: self.env.user.company_id.currency_id.id)

    order_line = fields.One2many('odooloc.order.line', 'order_id', string='Order Lines',
                                 states={'cancel': [('readonly', True)], 'confirm': [('readonly', True)]}, copy=True)

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('odooloc.order') or '/'
        return super(odoolocOrder, self).create(vals)

    @api.multi
    def action_confirm_order(self):
        self.write({'state': 'confirm'})
        return True

    @api.multi
    def action_cancel_order(self):
        return self.write({'state': 'cancel'})


class odoolocOrderLine(models.Model):
    _name = 'odooloc.order.line'
    # _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Rental order line"
    _order = 'order_id desc, name desc'

    @api.depends('product_qty', 'product_rental_price', 'taxes_id')
    def _compute_amount(self):
        for line in self:
            taxes = line.taxes_id.compute_all(line.product_rental_price, line.order_id.currency_id, line.product_qty,
                                              product=line.product_id, partner=line.order_id.customer_id)
            line.update({
                'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                'price_total': taxes['total_included'],
                'price_subtotal': taxes['total_excluded'],
            })

    name = fields.Text(string='Description') #TODO make it required
    sequence = fields.Integer(string='Sequence', default=10)
    product_qty = fields.Integer(string='Quantity', default=1)
    taxes_id = fields.Many2many('account.tax', string='Taxes',
                                domain=['|', ('active', '=', False), ('active', '=', True)])
    product_id = fields.Many2one('product.product', string='Product', domain=[('rental', '=', True)],
                                 change_default=True, required=True)

    product_rental_price = fields.Float(string='Unit price per day', required=True,
                                        digits=dp.get_precision('Rental price'), domain=[('rental'), '=', True])
    price_subtotal = fields.Monetary(compute='_compute_amount', string='Subtotal', store=True)
    price_total = fields.Monetary(compute='_compute_amount', string='Total', store=True)
    price_tax = fields.Float(compute='_compute_amount', string='Tax', store=True)

    order_id = fields.Many2one('odooloc.order', string='Order Reference', index=True, required=True,
                               ondelete='cascade')

    customer_id = fields.Many2one('res.partner', related='order_id.customer_id', string='Customer', readonly=True,
                                 store=True)
    currency_id = fields.Many2one(related='order_id.currency_id', store=True, string='Currency', readonly=True)


class MaintenanceEquipment(models.Model):
    _inherit = "maintenance.equipment"

    odooloc_reference_product_id = fields.Many2one('stock.production.lot', string='Reference product',
                                                   domain="[('name', '>', 0)]")


# Adding product rental price for rentable products
class ProductTemplate(models.Model):
    _inherit = "product.template"
    product_rental_price = fields.Float('Unit price per day', digits=dp.get_precision('Rental Price'),
                                        domain=[('rental', '=', True)])
