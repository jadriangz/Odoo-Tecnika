# -*- coding: utf-8 -*-
from odoo import models, fields
from odoo.exceptions import UserError


class AccountMoveInherit(models.Model):
    _inherit = 'account.move'

    custom_amount = fields.Float()
    custom_amount_status = fields.Char(default='not_changed')

    def custom_partial_reconciled(self, line_id, amount):
        move_line_id = self.env['account.move.line'].browse(line_id)
        move_line_id.move_id.write({'custom_amount': amount})
        move_line_id.move_id.custom_amount_status = 'changed'


class AccountMoveLineInherit(models.Model):
    _inherit = 'account.move.line'

    def _prepare_reconciliation_partials(self):
        flag = 0

        def fix_remaining_cent(currency, abs_residual, partial_amount):

            if abs_residual - currency.rounding <= partial_amount <= abs_residual + currency.rounding:
                return abs_residual
            else:
                return partial_amount

        debit_lines = iter(self.filtered(
            lambda line: line.balance > 0.0 or line.amount_currency > 0.0))
        credit_lines = iter(self.filtered(
            lambda line: line.balance < 0.0 or line.amount_currency < 0.0))
        debit_line = None
        credit_line = None

        debit_amount_residual = 0.0
        debit_amount_residual_currency = 0.0
        credit_amount_residual = 0.0
        credit_amount_residual_currency = 0.0
        debit_line_currency = None
        credit_line_currency = None

        partials_vals_list = []

        while True:

            if not debit_line:
                debit_line = next(debit_lines, None)
                if not debit_line:
                    break
                debit_amount_residual = debit_line.amount_residual

                if debit_line.currency_id:
                    debit_amount_residual_currency = debit_line.amount_residual_currency
                    debit_line_currency = debit_line.currency_id
                else:
                    debit_amount_residual_currency = debit_amount_residual
                    debit_line_currency = debit_line.company_currency_id

            if not credit_line:
                credit_line = next(credit_lines, None)
                if not credit_line:
                    break
                credit_amount_residual = credit_line.amount_residual

                if credit_line.currency_id:
                    credit_amount_residual_currency = credit_line.amount_residual_currency
                    credit_line_currency = credit_line.currency_id
                else:
                    credit_amount_residual_currency = credit_amount_residual
                    credit_line_currency = credit_line.company_currency_id

            min_amount_residual = min(debit_amount_residual,
                                      -credit_amount_residual)

            has_debit_residual_left = not debit_line.company_currency_id.is_zero(
                debit_amount_residual) and debit_amount_residual > 0.0
            has_credit_residual_left = not credit_line.company_currency_id.is_zero(
                credit_amount_residual) and credit_amount_residual < 0.0
            has_debit_residual_curr_left = not debit_line_currency.is_zero(
                debit_amount_residual_currency) and debit_amount_residual_currency > 0.0
            has_credit_residual_curr_left = not credit_line_currency.is_zero(
                credit_amount_residual_currency) and credit_amount_residual_currency < 0.0

            if debit_line_currency == credit_line_currency:

                if not has_debit_residual_curr_left and (
                        has_credit_residual_curr_left or not has_debit_residual_left):
                    debit_line = None
                    continue

                if not has_credit_residual_curr_left and (
                        has_debit_residual_curr_left or not has_credit_residual_left):
                    credit_line = None
                    continue

                min_amount_residual_currency = min(
                    debit_amount_residual_currency,
                    -credit_amount_residual_currency)
                min_debit_amount_residual_currency = min_amount_residual_currency
                min_credit_amount_residual_currency = min_amount_residual_currency

            else:

                if not has_debit_residual_left:
                    debit_line = None
                    continue

                if not has_credit_residual_left:
                    credit_line = None
                    continue

                min_debit_amount_residual_currency = credit_line.company_currency_id._convert(
                    min_amount_residual,
                    debit_line.currency_id,
                    credit_line.company_id,
                    credit_line.date,
                )
                min_debit_amount_residual_currency = fix_remaining_cent(
                    debit_line.currency_id,
                    debit_amount_residual_currency,
                    min_debit_amount_residual_currency,
                )
                min_credit_amount_residual_currency = debit_line.company_currency_id._convert(
                    min_amount_residual,
                    credit_line.currency_id,
                    debit_line.company_id,
                    debit_line.date,
                )
                min_credit_amount_residual_currency = fix_remaining_cent(
                    credit_line.currency_id,
                    -credit_amount_residual_currency,
                    min_credit_amount_residual_currency,
                )

            debit_amount_residual -= min_amount_residual
            debit_amount_residual_currency -= min_debit_amount_residual_currency
            credit_amount_residual += min_amount_residual
            credit_amount_residual_currency += min_credit_amount_residual_currency

            if debit_line.move_id.custom_amount_status == 'changed':
                if debit_line.amount_residual >= debit_line.move_id.custom_amount:
                    partials_vals_list.append({
                        'amount': debit_line.move_id.custom_amount,
                        'debit_amount_currency': debit_line.move_id.custom_amount,
                        'credit_amount_currency': debit_line.move_id.custom_amount,
                        'debit_move_id': debit_line.id,
                        'credit_move_id': credit_line.id,
                    })
                    debit_line.move_id.custom_amount_status = 'not_changed'
                else:
                    flag = 1
                    debit_line.move_id.custom_amount_status = 'not_changed'
            else:
                partials_vals_list.append({
                    'amount': min_amount_residual,
                    'debit_amount_currency': min_debit_amount_residual_currency,
                    'credit_amount_currency': min_credit_amount_residual_currency,
                    'debit_move_id': debit_line.id,
                    'credit_move_id': credit_line.id,
                })

        if flag == 1:
            pass
        else:
            return partials_vals_list
