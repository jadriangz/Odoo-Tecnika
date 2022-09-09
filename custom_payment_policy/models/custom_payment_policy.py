# -*- coding: utf-8 -*-
from odoo import models, fields,api


class AccountMoveInheritPaymentPolicy(models.Model):
    _inherit = 'account.move'

    custom_l10n_mx_edi_payment_policy = fields.Selection(string='Payment Policy',
                                                  selection=[('PPD', 'PPD'),
                                                             ('PUE', 'PUE')])

    @api.depends('move_type', 'company_id', 'state')
    def _compute_l10n_mx_edi_cfdi_request(self):
        for move in self:
            if move.country_code != 'MX':
                move.l10n_mx_edi_cfdi_request = False
            elif move.move_type == 'out_invoice':
                move.l10n_mx_edi_cfdi_request = 'on_invoice'
            elif move.move_type == 'out_refund':
                move.l10n_mx_edi_cfdi_request = 'on_refund'
            elif (
                    move.payment_id and move.payment_id.payment_type == 'inbound' and
                    'PPD' in move._get_reconciled_invoices().mapped(
                'custom_l10n_mx_edi_payment_policy')):
                move.l10n_mx_edi_cfdi_request = 'on_payment'
            elif move.statement_line_id:
                move.l10n_mx_edi_cfdi_request = 'on_payment'
            else:
                move.l10n_mx_edi_cfdi_request = False