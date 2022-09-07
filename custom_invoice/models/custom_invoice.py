# -*- coding: utf-8 -*-
from odoo import models,fields


class AccountMoveInherit(models.Model):
    _inherit = 'account.move'

    def update_invoice_line(self):
        return {
            'name': 'Invoice Line',
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'custom.invoice.wizard',
            'type': 'ir.actions.act_window',
            'target': 'new',
        }

