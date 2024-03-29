# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.tools import float_compare
from odoo.exceptions import UserError, ValidationError
from odoo.addons import decimal_precision as dp
from datetime import datetime


class odoolocOrder(models.Model):
    _name = 'odooloc.order'
    _description = "Rental order"
    _order = 'name desc'

    @api.depends('order_line.price_subtotal', 'nb_days')
    def _amount_all(self):
        for order in self:
            amount_daily = 0.0
            for line in order.order_line:
                amount_daily += line.price_subtotal
                order._compute_nb_days()
            order.update({
                'amount_daily': amount_daily,
                'amount_total': (amount_daily) * order.nb_days,
            })

    @api.depends('date_start', 'date_end')
    def _compute_nb_days(self):
        for order in self:
            format = '%Y-%m-%d'
            d1 = datetime.strptime(order.date_end, format)
            d2 = datetime.strptime(order.date_start, format)
            nb_days = str((d1 - d2).days + 1)
            order.update({'nb_days': nb_days})

    @api.onchange('date_end', 'date_start', 'date_order', 'confirmation_date')
    def _check_dates(self):
        format = '%Y-%m-%d'
        formatdt = '%Y-%m-%d %H:%M:%S'
        cd_date_start = datetime.strptime(self.date_start, format).date()
        cd_date_end = datetime.strptime(self.date_end, format).date()
        cd_datetime_order = self.date_order
        cd_date_order = datetime.strptime(cd_datetime_order, formatdt).date()
        cd_datetime_confirmation = self.date_order
        cd_date_confirmation = datetime.strptime(cd_datetime_confirmation, formatdt).date()

        if cd_date_end < cd_date_start:
            raise ValidationError('Start date can not be bigger than end date!')
        elif cd_date_start < cd_date_order:
            raise ValidationError('Start date can not be smaller than order date!')
        elif cd_datetime_confirmation < cd_datetime_order:
            raise ValidationError('Confirmation date can not be smaller than order date!')
        elif cd_date_confirmation > cd_date_start:
            raise ValidationError('Confirmation date can not be bigger than start date!')

    name = fields.Char('Rental Reference', required=True, index=True, copy=False, default='New')
    sequence = fields.Integer('Sequence', default=1,
                              help='Gives the sequence order when displaying a rental order list')
    confirmation_date = fields.Datetime('Confirmation date', readonly=True, index=True,
                                        help="Date on which the rental order is confirmed.", copy=False)
    date_start = fields.Date('Start date', required=True, index=True, copy=False, default=fields.Date.today())
    date_end = fields.Date('End date', required=True, index=True, copy=False, default=fields.Date.today())
    date_out = fields.Datetime('Picking OUT date', required=True, index=True, copy=False, default=fields.Datetime.now)
    date_in = fields.Datetime('Picking IN date', required=True, index=True, copy=False, default=fields.Datetime.now)
    nb_days = fields.Integer(string='Number of rental days', store=True, readonly=True, compute='_compute_nb_days')
    event_name = fields.Char('Event name')
    event_adress = fields.Char('Event adress')
    event_zip = fields.Char('Event ZIP')
    event_city = fields.Char('Event city')
    comment = fields.Char('Comments')
    pick_method = fields.Boolean('Self-service delivery')
    access_nip = fields.Char('Access NIP')
    assembly_method = fields.Boolean('Self-service assembly')
    state = fields.Selection([
        ('draft', 'Quotation'),
        ('sent', 'Quotation Sent'),
        ('rent', 'Rental Order'),
        ('done', 'Done'),
        ('cancel', 'Canceled')
    ], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', default='draft')
    date_order = fields.Datetime(string='Order date', required=True, readonly=True, index=True,
                                 states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}, copy=False,
                                 default=fields.Datetime.now)
    user_id = fields.Many2one('res.users', string='Rentalsperson', index=True, track_visibility='onchange',
                              default=lambda self: self.env.user)
    partner_id = fields.Many2one('res.partner', string='Customer', readonly=True,
                                 states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}, required=True,
                                 index=True, track_visibility='always')
    partner_invoice_id = fields.Many2one('res.partner', string='Invoice Address', readonly=True, required=True,
                                         states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},
                                         help="Invoice address for current rentals order.")
    partner_shipping_id = fields.Many2one('res.partner', string='Delivery Address', readonly=True, required=True,
                                          states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},
                                          help="Delivery address for current rentals order.")
    pricelist_id = fields.Many2one('product.pricelist', string='Pricelist', required=True, readonly=True,
                                   states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},
                                   help="Pricelist for current rentals order.")
    currency_id = fields.Many2one("res.currency", related='pricelist_id.currency_id', string="Currency", readonly=True,
                                  required=True)
    order_line = fields.One2many('odooloc.order.line', 'order_id', string='Order Lines',
                                 states={'cancel': [('readonly', True)], 'confirm': [('readonly', True)]}, copy=True)
    company_id = fields.Many2one('res.company', 'Company',
                                 default=lambda self: self.env['res.company']._company_default_get('odooloc.order'))
    note = fields.Text('Terms and conditions')
    amount_daily = fields.Monetary(string='Total per day', store=True, readonly=True, compute='_amount_all')
    amount_total = fields.Monetary(string='Total', store=True, readonly=True, compute='_amount_all',
                                   track_visibility='always')

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
    def odooloc_print_quotation(self):
        self.filtered(lambda s: s.state == 'draft').write({'state': 'sent'})

    @api.multi
    def odooloc_draft_order(self):
        orders = self.filtered(lambda s: s.state in ['cancel', 'sent'])
        return orders.write({
            'state': 'draft',
        })

    @api.multi
    def odooloc_cancel_order(self):
        return self.write({'state': 'cancel'})

    @api.multi
    def odooloc_send_quotation(self):
        self._check_dates()
        self.filtered(lambda s: s.state == 'draft').write({'state': 'sent'})
        '''
                This function opens a window to compose an email, with the edi sale template message loaded by default
                '''
        self.ensure_one()
        # ir_model_data = self.env['ir.model.data']
        # try:
        #     template_id = ir_model_data.get_object_reference('odooloc', 'email_template_edi_odooloc')[1]
        # except ValueError:
        #     template_id = False
        # try:
        #     compose_form_id = ir_model_data.get_object_reference('mail', 'email_compose_message_wizard_form')[1]
        # except ValueError:
        #     compose_form_id = False
        # ctx = {
        #     'default_model': 'odooloc.order',
        #     'default_res_id': self.ids[0],
        #     'default_use_template': bool(template_id),
        #     'default_template_id': template_id,
        #     'default_composition_mode': 'comment',
        #     'mark_so_as_sent': True,
        #     'custom_layout': "odooloc.mail_template_data_notification_email_sale_order",
        #     'proforma': self.env.context.get('proforma', False),
        #     'force_email': True
        # }
        # return {
        #     'type': 'ir.actions.act_window',
        #     'view_type': 'form',
        #     'view_mode': 'form',
        #     'res_model': 'mail.compose.message',
        #     'views': [(compose_form_id, 'form')],
        #     'view_id': compose_form_id,
        #     'target': 'new',
        #     'context': ctx,
        # }

    @api.multi
    def odooloc_lock_order(self):
        return self.write({'state': 'done'})

    @api.multi
    def odooloc_unlock_order(self):
        self.write({'state': 'rent'})

    @api.multi
    def _odooloc_confirm_order(self):
        self._check_dates()
        self.write({
            'state': 'rent',
            'confirmation_date': fields.Datetime.now()
        })
        return True

    @api.multi
    def odooloc_confirm_order(self):
        if self._get_forbidden_state_confirm() & set(self.mapped('state')):
            raise UserError(_(
                'It is not allowed to confirm an order in the following states: %s'
            ) % (', '.join(self._get_forbidden_state_confirm())))
        self._odooloc_confirm_order()
        return True

    def _get_forbidden_state_confirm(self):
        return {'done', 'cancel'}


class odoolocOrderLine(models.Model):
    _name = 'odooloc.order.line'
    _description = "Rental order line"
    _order = 'order_id desc, name desc'

    @api.depends('product_uom_qty', 'rental_price')
    def _compute_amount(self):
        for line in self:
            price_subtotal = line.rental_price * line.product_uom_qty
            line.update({
                'price_subtotal': price_subtotal,
            })

    @api.model
    def _prepare_add_missing_fields(self, values):
        """ Deduce missing required fields from the onchange """
        res = {}
        onchange_fields = ['name', 'rental_price', 'product_uom']
        if values.get('order_id') and values.get('product_id') and any(f not in values for f in onchange_fields):
            line = self.new(values)
            line.on_change_product_id()
            for field in onchange_fields:
                if field not in values:
                    res[field] = line._fields[field].convert_to_write(line[field], line)
        return res

    @api.model
    def create(self, values):
        values.update(self._prepare_add_missing_fields(values))
        line = super(odoolocOrderLine, self).create(values)
        if line.order_id.state == 'rent':
            raise ValidationError('You can not add a product when order is confirmed!')
        return line

    @api.multi
    def write(self, values):
        if 'product_uom_qty' in values:
            precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
            self.filtered(
                lambda r: r.state == 'rent' and float_compare(r.product_uom_qty, values['product_uom_qty'],
                                                              precision_digits=precision) != 0)._update_line_quantity(
                values)

        # Prevent writing on a locked SO.
        protected_fields = self._get_protected_fields()
        if 'done' in self.mapped('order_id.state') and any(f in values.keys() for f in protected_fields):
            protected_fields_modified = list(set(protected_fields) & set(values.keys()))
            fields = self.env['ir.model.fields'].search([
                ('name', 'in', protected_fields_modified), ('model', '=', self._name)
            ])
            raise UserError(
                _('It is forbidden to modify the following fields in a locked order:\n%s')
                % '\n'.join(fields.mapped('field_description'))
            )
        result = super(odoolocOrderLine, self).write(values)
        return result

    order_id = fields.Many2one('odooloc.order', string='Order Reference', index=True, required=True,
                               ondelete='cascade')
    name = fields.Text(string='Description', required=True)
    sequence = fields.Integer(string='Sequence', default=10)
    rental_price = fields.Float(string='Unit price per day', required=True,
                                digits=dp.get_precision('Rental price'), domain=[('rental'), '=', True])
    price_subtotal = fields.Monetary(compute='_compute_amount', string='Subtotal', readonly=True, store=True)
    product_id = fields.Many2one('product.template', string='Product', domain=[('rental', '=', True)],
                                 change_default=True, required=True)
    product_uom_qty = fields.Float(string='Quantity', digits=dp.get_precision('Product Unit of Measure'), required=True,
                                   default=1.0)
    product_uom = fields.Many2one('product.uom', string='Unit of Measure', required=True)
    rentalsman_id = fields.Many2one(related='order_id.user_id', store=True, string='Rentalsperson', readonly=True)
    currency_id = fields.Many2one(related='order_id.currency_id', store=True, string='Currency', readonly=True)
    company_id = fields.Many2one(related='order_id.company_id', string='Company', store=True, readonly=True)
    order_partner_id = fields.Many2one(related='order_id.partner_id', store=True, string='Customer')
    state = fields.Selection([
        ('draft', 'Quotation'),
        ('sent', 'Quotation Sent'),
        ('rent', 'Rentals Order'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
    ], related='order_id.state', string='Order Status', readonly=True, copy=False, store=True, default='draft')

    @api.multi
    @api.onchange('product_id')
    def on_change_product_id(self):
        vals = {}
        if not self.product_uom or self.product_id.uom_id.id != self.product_uom.id:
            vals['product_uom'] = self.product_id.uom_id
            vals['product_uom_qty'] = 1.0
        if not self.name or self.name != self.product_id.name:
            vals['name'] = self.product_id.name
        res = {
            'value': {
                'rental_price': self.product_id.rental_price,
                'product_uom': self.product_id.uom_id
            }
        }
        self.update(vals)
        return res

    def _get_protected_fields(self):
        return [
            'product_id', 'name', 'rental_price', 'product_uom', 'product_uom_qty',
        ]


    def myFunction(self,param1,param2):
        variable = param1+param2
        return variable