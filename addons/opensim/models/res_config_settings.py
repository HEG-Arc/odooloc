from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    chart_of_account_installed = fields.Boolean(default=False)

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        res.update(
            chart_of_account_installed=False,
        )
        return res

    @api.multi
    def set_values(self):
        super(ResConfigSettings, self).set_values()
        self.env.ref('opensim.mail_alias_expense').write({'alias_name': self.expense_alias_prefix})
        self.env['ir.config_parameter'].sudo().set_param('hr_expense.use_mailgateway', self.use_mailgateway)

    @api.onchange('use_mailgateway')
    def _onchange_use_mailgateway(self):
        if not self.use_mailgateway:
            self.expense_alias_prefix = False
