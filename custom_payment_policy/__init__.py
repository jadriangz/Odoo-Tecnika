# -*- coding: utf-8 -*-
from . import models
from odoo import api, SUPERUSER_ID


def _post_init_payment_policy(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    account_move_data = env['account.move'].search(
        [('move_type', '=', 'out_invoice')])
    for move in account_move_data:
        if move.is_invoice(include_receipts=True) and move.invoice_date_due and move.invoice_date:
            if move.move_type == 'out_invoice':
                if move.invoice_date_due.month > move.invoice_date.month or move.invoice_date_due.year > move.invoice_date.year or len(move.invoice_payment_term_id.line_ids) > 1:
                    move.custom_l10n_mx_edi_payment_policy = 'PPD'
                else:
                    move.custom_l10n_mx_edi_payment_policy = 'PUE'
            else:
                move.custom_l10n_mx_edi_payment_policy = 'PUE'
        else:
            move.custom_l10n_mx_edi_payment_policy = False
