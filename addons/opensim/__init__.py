# -*- coding: utf-8 -*-

from . import controllers
from . import models
from odoo import api, SUPERUSER_ID


def post_init_hook(cr, registry):
    import logging
    _logger = logging.getLogger(__name__)
    env = api.Environment(cr, SUPERUSER_ID, {})
    _logger.info('post_init_hook calling opensim.install_chart_of_account()')
    env['opensim.opensim'].install_chart_of_account()

def resume_simulation_thread():
    models.models.opensim.start_simulation_thread(True)
