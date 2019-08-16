# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from odoo.addons import decimal_precision as dp
from odoo import models, fields, api


class odoolocOrder(models.Model):
    _name = 'odooloc.order'
    _inherit = 'sale.order'
    _description = "Rental order"
    _order = 'name desc'

    READONLY_STATES = {
        'confirm': [('readonly', True)],
        'cancel': [('readonly', True)],
    }

    name = fields.Char('Rental Reference', required=True, index=True, copy=False, default='New')
    sequence = fields.Integer('Sequence', default=1,
                              help='Gives the sequence order when displaying a rental order list')

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
        ('draft', 'Quotation'),
        ('sent', 'Quotation Sent'),
        ('sale', 'Rental Order'),
        ('rental', 'Rental'),
        ('done', 'Done'),
        ('cancel', 'Canceled')
    ], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', default='draft')

    picking_state = fields.Selection([
        ('none', 'No picking status'),
        ('picking', 'Preparing items'),
        ('picked', 'Items Ready'),
        ('handed', 'Handed to Customer'),
        ('back', 'Back to Company')
    ], string='Picking Status', readonly=True, copy=False, index=True, track_visibility='onchange', default='none')

    order_line = fields.One2many('odooloc.order.line', 'order_id', string='Order Lines',
                                 states={'cancel': [('readonly', True)], 'confirm': [('readonly', True)]}, copy=True)

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            if 'company_id' in vals:
                vals['name'] = self.env['ir.sequence'].with_context(force_company=vals['company_id']).next_by_code(
                    'odooloc.order') or '/'
            else:
                vals['name'] = self.env['ir.sequence'].next_by_code('odooloc.order') or '/'

        # Makes sure partner_invoice_id', 'partner_shipping_id' and 'pricelist_id' are defined
        if any(f not in vals for f in ['partner_invoice_id', 'partner_shipping_id', 'pricelist_id']):
            partner = self.env['res.partner'].browse(vals.get('partner_id'))
            addr = partner.address_get(['delivery', 'invoice'])
            vals['partner_invoice_id'] = vals.setdefault('partner_invoice_id', addr['invoice'])
            vals['partner_shipping_id'] = vals.setdefault('partner_shipping_id', addr['delivery'])
            vals['pricelist_id'] = vals.setdefault('pricelist_id',
                                                   partner.property_product_pricelist and partner.property_product_pricelist.id)
        result = super(odoolocOrder, self).create(vals)
        return result

    @api.multi
    def _action_confirm(self):
        for order in self.filtered(lambda order: order.partner_id not in order.message_partner_ids):
            order.message_subscribe([order.partner_id.id])
        self.write({
            'state': 'sale',
            'confirmation_date': fields.Datetime.now()
        })
        if self.env.context.get('send_email'):
            self.force_quotation_send()

        # # create an analytic account if at least an expense product
        # for order in self:
        #     if any([expense_policy not in [False, 'no'] for expense_policy in
        #             order.order_line.mapped('product_id.expense_policy')]):
        #         if not order.analytic_account_id:
        #             order._create_analytic_account()

        return True

    @api.multi
    def action_picking(self):
        self.write({
            'state': 'rental',
            'picking_state': 'picking'
        })


class odoolocOrderLine(models.Model):
    _name = 'odooloc.order.line'
    _inherit = 'sale.order.line'
    _description = "Rental order line"
    _order = 'order_id desc, name desc'

    name = fields.Text(string='Description', required=True)

    product_id = fields.Many2one('product.product', string='Product', domain=[('rental', '=', True)],
                                 change_default=True, required=True)

    price_unit = fields.Float(string='Unit price per day', required=True,
                              digits=dp.get_precision('Rental price'), domain=[('rental'), '=', True])

    order_id = fields.Many2one('odooloc.order', string='Order Reference', index=True, required=True,
                               ondelete='cascade')


class MaintenanceEquipment(models.Model):
    _inherit = "maintenance.equipment"

    odooloc_reference_product_id = fields.Many2one('stock.production.lot', string='Reference product',
                                                   domain="[('name', '>', 0)]")


# Adding product rental price for rentable products
class ProductTemplate(models.Model):
    _inherit = "product.template"
    rental_price_unit = fields.Float('Unit price per day', digits=dp.get_precision('Rental Price'),
                                     domain=[('rental', '=', True)])
