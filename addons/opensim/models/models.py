# -*- coding: utf-8 -*-
import json
import random

import odoo
from odoo import models, fields, api
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT
from odoo.tools import  DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT
from datetime import datetime, timedelta
import time
import logging, threading

from odoo.addons.opensim_time.models.models import OpensimTime

_logger = logging.getLogger(__name__)

class opensim(models.Model):
    _name = 'opensim.opensim'
    name = fields.Char()
    start_date = fields.Datetime(default=fields.Datetime.now.super)
    resume_start_date = fields.Datetime(string='Simulation "calculated" start Date on resume')
    end_date = fields.Datetime(string='Simulation end Date')
    duration = fields.Integer(compute="_value_duration", string='Duration (min)')
    paused = fields.Boolean(string='Paused', readonly=True, store=True)
    state = fields.Selection([
        ('ready', 'ready'),
        ('running', 'Running'),
        ('paused', 'Paused'),
        ('ended', 'Ended')
    ], compute='_compute_state', string='Status', copy=False, index=True, readonly=True, store=True,
        help="Status of the simulation.")

    _simulation_thread_exit_cond = None

    @api.depends('resume_start_date','end_date')
    def _value_duration(self):
        for record in self:
            if not record.resume_start_date:
                record.duration = 0
            else:
                end_date = fields.Datetime.from_string(record.end_date) if record.end_date else datetime.now()
                record.duration = (end_date - fields.Datetime.from_string(record.resume_start_date)).seconds / 60

    @api.multi
    def now(self, *args):
        """ Define our own datetime.now to replace odoo's fields.Datetime.now static method that
            is used in all modules to get current date.

            Return the current Simulation's day and time in the format expected by the ORM.
            This function may be used to compute default values.
        """
        running = self.search([('state', 'in', ['running','paused'])])
        running.ensure_one()
        # hard coded "time speed" for now 1 day passes every minute
        simulation_now = datetime.now() + timedelta(days=running.duration)
        return simulation_now.strftime(DATETIME_FORMAT)

    @api.multi
    def today(self, *args):
        """ Return the current day in the format expected by the ORM.
            This function may be used to compute default values.
        """
        self.ensure_one()
        return fields.Datetime.from_string(self.now()).strftime(DATE_FORMAT)

    @api.model
    def banner_data(self,env=None):
        """ called by banner Widget
            Finds if there is an active simulation
            and return corresponding simulation date, duration and company name
        """
        user_company = self.env.user.company_id.name if env is None else None
        env = env or self.env
        active_one = env['opensim.opensim'].search([('state', 'in', ['running', 'paused'])])
        if len(active_one)==1:
            return dict(active=True, team=user_company, today=OpensimTime.today().strftime(DATE_FORMAT), duration=OpensimTime.duration().seconds//60)
        else:
            return dict(active = False, team=user_company, today='',duration='')

    @api.depends('start_date', 'end_date')
    def _compute_state(self):
        for record in self:
            if not record.start_date:
                record.state = "ready"
            elif record.end_date:
                if record.paused:
                    record.state = "paused"
                else:
                    record.state = "ended"
            else:
                record.state = "running"

    @api.multi
    @api.returns('self')
    def start(self):
        self.ensure_one()
        for simulation in self:
            _logger.info('start simulation: {}'.format(simulation))
            start_date = datetime.now()
            OpensimTime.reset_start_time(start_date)
            str_start_date=start_date.strftime(DATETIME_FORMAT)
            simulation.write(dict(start_date=str_start_date, resume_start_date=str_start_date, paused=False, end_date=None))
        return self

    @api.multi
    @api.returns('self')
    def stop(self):
        for simulation in self:
            _logger.info('stop simulation: {}'.format(simulation))
            if simulation.state in ('running','paused'):
                OpensimTime.stop()
                if simulation.state == 'running':
                    self.stop_simulation_thread()
            simulation.write(dict(end_date=fields.Datetime.now.super(), paused=False))
        return self

    @api.multi
    @api.returns('self')
    def pause(self):
        for simulation in self:
            _logger.info('pause simulation: {}'.format(simulation))
            end_date = fields.Datetime.now.super()
            self.stop_simulation_thread()
            OpensimTime.pause(fields.Datetime.from_string(end_date))
            simulation.write(dict(end_date=end_date, paused=True))

        return self

    @api.multi
    @api.returns('self')
    def resume(self):
        self.ensure_one()
        for simulation in self:
            _logger.info('resume simulation: {} start{} -> end{}'.format(simulation,simulation.resume_start_date, simulation.end_date))
            end_date = fields.Datetime.from_string(simulation.end_date)
            resume_start_date = fields.Datetime.from_string(simulation.resume_start_date)
            if end_date: # resume from actual pause
                duration_on_pause = (end_date - resume_start_date).seconds
                # calculate new resume_start_date for simulation to resume with same duration as when it was paused
                resume_start_date = datetime.now() - timedelta(seconds=duration_on_pause)
            # else:
            #    resume previously interrupted simulation on server startup\
            # we modify the module variable on resume as there could be only one simulation active at any time
            # and we want to avoid simulationtime_now
            OpensimTime.reset_start_time(resume_start_date)

            _logger.info('duration when paused: {}s - resume_start_date={}'.format(duration_on_pause, resume_start_date))
            simulation.write(dict(resume_start_date=resume_start_date.strftime(DATETIME_FORMAT),end_date=None,paused=False))
        self.start_simulation_thread()
        return self

    @api.model
    def create(self, vals):
        """
        override create to start simulation_thread when instance is created with start_date (default creation)
        :param vals:
        :return:
        """
        # copy start_date to resume_start_date on create
        if vals.get('start_date') and not vals.get('resume_start_date'):
            vals['resume_start_date'] = vals['start_date']
        instance = super(opensim, self).create(vals)

        if vals.get('start_date'):
            start_date = fields.Datetime.from_string(vals['start_date'])
            OpensimTime.reset_start_time(start_date)
            instance.start_simulation_thread()
        return instance

    @api.model
    @api.returns('self')
    def stop_all(self):
        _logger.info('stop_all called')
        active_simulations = self.search([('end_date', '=', False)], order='start_date desc')
        for simulation in active_simulations:
            _logger.info('simulations: {}'.format(simulation))
            simulation.end_date = fields.Datetime.now.super()
            simulation.paused = False
        return active_simulations

    @api.model
    def install_chart_of_account(self):
        """
        install utility method called from function.xml allowing re-installation of chart of account module
        after company creation through res.company.csv loading
        thus installing chart of account in all companies
        :return: None
        """
        company_list = self.env['res.company'].search([
            ('id', '!=', self.env.user.company_id.id)
        ])
        # if any of the initial companies does not have chart of account
        if any(not company.chart_template_id for company in company_list):
            # upgrade chart of account module
            self.env.ref('base.module_l10n_ch').button_immediate_upgrade()

    @classmethod
    def create_sale_order(cls, env, company, product, quantity):
        """
         Create sale order, for product*quantity from Coffee Shop customer (opensim.res_partner_customer1)
         to company (A/B)
         Move stock items, and confirm payment
        :return: None
        """
        company_user = env['res.users'].search([('company_id', '=', company.id)],limit=1)
        order = env['sale.order'].sudo(company_user.id).create({'partner_id': env.ref('opensim.res_partner_customer1').id})
        ol1 = env['sale.order.line'].sudo(company_user.id).create(dict(order_id=order.id, product_id=product.id, product_uom_qty=quantity))
        order.action_confirm()
        invoice_ids = order.action_invoice_create(final=True)
        invoices = env['account.invoice'].browse(invoice_ids)
        invoices.action_invoice_open()
        invoices.pay_and_reconcile(env['account.journal'].sudo(company_user.id).search([('type', '=', 'bank')], limit=1))
        invoices.action_invoice_paid()

        # move stock items line in order
        for ml in order.picking_ids.move_lines:
            ml.quantity_done=ml.product_uom_qty
        order.picking_ids.action_done()

        _logger.info('create_sale_order for {} qty={} {}'.format(product.display_name,quantity, invoices.display_name))

    @classmethod
    def sim_customer_purchases(cls, env):
        """
        check available stock quantity for company A or B
        then create/deliver and pay 1 sale order for each available product (with random quantity).
        :param env:
        :return:
        """
        for sq in env['stock.quant'].search([('company_id', 'in', ("A","B"))]):
            purchase_qty = random.randint(10, 30) if  sq.quantity > 30 else sq.quantity
            cls.create_sale_order(env,sq.company_id,sq.product_id,purchase_qty)


    @classmethod
    def get_order_delay(cls, po):
        """
        :param po: purchase order singleton recordset
        :return: delay for whole purchase order (maximum delay of all its order lines)
        """
        po.ensure_one()
        def order_line_delays(po):
            """
            purchase order lines delay generator
            :param po: purchase order singleton recordset
            :yield:  delay of each po's order lines
            """
            for ol in po.order_line:
                supplierinfo = ol.product_id.seller_ids.search(
                    [('name', '=', ol.partner_id.name), ('product_tmpl_id', '=', ol.product_id.product_tmpl_id.id),
                     ('company_id', '=', ol.company_id.id), ('min_qty', '<=', ol.product_qty)], order='delay desc', limit=1)
                _logger.info('{} {} #{}  min_qty={} delay={}'.format(ol, ol.name, ol.product_qty, supplierinfo.min_qty,
                                                                 supplierinfo.delay))
                yield supplierinfo.delay
        return max(order_line_delays(po))

    @classmethod
    def sim_receive_products(cls, env):
        # search for pending purchase orders
        # picking_ids.state
        # for po in env['purchase.order'].search([('picking_ids.state','not in',('done','cancel') )]): # => picking_ids.state = 'assigned'
        for po in env['purchase.order'].search(
                [('picking_ids.state', '=', 'assigned')]):
            _logger.info('sim_receive_products {} date_order:{}'.format(po,po.date_order))
            delay = cls.get_order_delay(po)
            _logger.info('{} delay = {}'.format(po,delay))
            if OpensimTime.now() > fields.Datetime.from_string(po.date_order) + timedelta(days=delay):
                _logger.info('simulation time={} passed delay -  starting immediate stock transfer'.format(fields.Datetime.now()))
                stock_transfer_wizard = po.picking_ids.button_validate()
                if stock_transfer_wizard.get('res_id'):
                    stock_transfer = env['stock.immediate.transfer'].browse(stock_transfer_wizard.get('res_id'))
                    stock_transfer.process()
    @classmethod
    def sim_bill_products(cls, env):
        for po in env['purchase.order'].search(
            ['|',('picking_ids.state', '=', 'done'),('picking_ids', '=', False),
             ('invoice_status','=','to invoice')]):
            _logger.info('sim_bill_products {}-{}'.format(po, po.display_name))

            # we're going to create bill as the user who created the purchase order
            bill_user_id = po.create_uid.id
            bill = env['account.invoice'].sudo(bill_user_id).create(
                dict(type='in_invoice', account_id=240, partner_id=po.partner_id.id, purchase_id=po.id))
            # add po's lines to bill
            bill.purchase_order_change()
            # confirm invoice
            bill.action_invoice_open()
            # pay it
            # register payment action id 152
            bill.pay_and_reconcile(env['account.journal'].sudo(bill_user_id).search([('type', '=', 'bank')], limit=1))
            # creates an account.payment => action action_validate_invoice_payment
            bill.action_invoice_paid()

    @classmethod
    def run_simulation(cls,exit_condition, on_startup=False):
        # see cron_thread
        if on_startup:
            # fixme waiting (arbitrary 3s) for registry to be ready
            time.sleep(6)
        registries = odoo.modules.registry.Registry.registries
        for db_name, registry in registries.items():
            _logger.info('run_simulation for db_name={}'.format(db_name))
            if registry.ready:
                thread_cr = None
                try:
                    #see ir_cron._acquire_job -> _process_jobs
                    db = odoo.sql_db.db_connect(db_name)
                    threading.current_thread().dbname = db_name
                    thread_cr = db.cursor()
                    with api.Environment.manage():
                        env = api.Environment(thread_cr, 1, {})
                        l=0
                        active_one = env['opensim.opensim'].search([('state', 'in', ['running', 'paused'])])
                        if on_startup:
                            OpensimTime.reset_start_time(fields.Datetime.from_string(active_one.resume_start_date))
                        if len(active_one) == 1:
                            with exit_condition:
                                while True:
                                    try:
                                        # thread processing
                                        _logger.info('simulation thread for simulation({}) loop#{}'.format(active_one.id, l))

                                        cls.sim_customer_purchases(env)
                                        thread_cr.commit()

                                        cls.sim_receive_products(env)
                                        thread_cr.commit()

                                        cls.sim_bill_products(env)
                                        thread_cr.commit()

                                        # notify web client of banner update
                                        channel = ('odoo', 'opensim.opensim', 'banner')
                                        message = active_one.banner_data(env)
                                        _logger.info('bus send [{}] => {}'.format(channel,message))
                                        env['bus.bus'].sendone(channel,message)
                                        thread_cr.commit()

                                    except Exception as e:
                                        _logger.warning('run_simulation%d inner loop encountered an Exception: %s', active_one.id, e, exc_info=True)

                                    next_day_timeout = OpensimTime.until_tomorrow()
                                    _logger.info('next_day_timeout={}s => {}'.format(next_day_timeout,(datetime.now()+timedelta(seconds=next_day_timeout)).strftime(DATETIME_FORMAT)))
                                    # termination check
                                    if exit_condition.wait(timeout=next_day_timeout):
                                        _logger.info('simulation thread for simulation({}) terminating'.format(active_one.id))
                                        break
                                    _logger.info('exit_condition timed out at {} => simulation date: {}'.format(datetime.now().strftime(
                                        DATETIME_FORMAT), fields.Date.today()))
                                    l += 1
                        else:
                            _logger.info('run_simulation: no active simulation found exiting')
                except Exception as e:
                    _logger.warning('run_simulation%d encountered an Exception: %s', active_one.id, e, exc_info=True)
                finally:
                    if thread_cr:
                        # thread_cr.commit()
                        thread_cr.close()
            else:
                _logger.error('run_simulation %s registry %s not ready - aborting', db_name, registry)
            _logger.debug('run_simulation terminated')


    @classmethod
    def start_simulation_thread(cls,on_server_startup=False):
        if cls._simulation_thread_exit_cond is None:
            cls._simulation_thread_exit_cond = threading.Condition()
        threaded_simulation = threading.Thread(target=cls.run_simulation,daemon=True,args=(cls._simulation_thread_exit_cond,),
                                               kwargs={'on_startup':on_server_startup})
        _logger.info('start_simulation_thread')
        threaded_simulation.start()

    @classmethod
    def stop_simulation_thread(cls):
        if cls._simulation_thread_exit_cond:
            with cls._simulation_thread_exit_cond:
                cls._simulation_thread_exit_cond.notify()


