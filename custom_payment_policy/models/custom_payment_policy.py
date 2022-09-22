# -*- coding: utf-8 -*-
from odoo import models, fields, api
import re
from lxml import etree
from dateutil import tz


class AccountMoveInheritPaymentPolicy(models.Model):
    _inherit = 'account.move'

    custom_l10n_mx_edi_payment_policy = fields.Selection(
        string='Payment Policy',
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
                    move.payment_id and move.payment_id.payment_type == 'inbound' and 'PPD' in move._get_reconciled_invoices().mapped(
                'custom_l10n_mx_edi_payment_policy')):
                move.l10n_mx_edi_cfdi_request = 'on_payment'
            elif move.statement_line_id:
                move.l10n_mx_edi_cfdi_request = 'on_payment'
            else:
                move.l10n_mx_edi_cfdi_request = False


class AccountEdiFormatInheritPaymentPolicy(models.Model):
    _inherit = 'account.edi.format'

    def _l10n_mx_edi_get_invoice_cfdi_values(self, invoice):
        res = super(AccountEdiFormat,self)._l10n_mx_edi_get_invoice_cfdi_values(invoice)
        res.update({'payment_policy': invoice.custom_l10n_mx_edi_payment_policy})
        return res

    def _l10n_mx_edi_export_payment_cfdi(self, move):
        if move.payment_id:
            currency = move.payment_id.currency_id
            total_amount = move.payment_id.amount
        else:
            if move.statement_line_id.foreign_currency_id:
                total_amount = move.statement_line_id.amount_currency
                currency = move.statement_line_id.foreign_currency_id
            else:
                total_amount = move.statement_line_id.amount
                currency = move.statement_line_id.currency_id

        invoice_vals_list = []
        pay_rec_lines = move.line_ids.filtered(
            lambda line: line.account_internal_type in (
                'receivable', 'payable'))
        paid_amount = abs(sum(pay_rec_lines.mapped('amount_currency')))

        mxn_currency = self.env["res.currency"].search([('name', '=', 'MXN')],
                                                       limit=1)
        if move.currency_id == mxn_currency:
            rate_payment_curr_mxn = None
            paid_amount_comp_curr = paid_amount
        else:
            rate_payment_curr_mxn = move.currency_id._convert(1.0, mxn_currency,
                                                              move.company_id,
                                                              move.date,
                                                              round=False)
            paid_amount_comp_curr = move.company_currency_id.round(
                paid_amount * rate_payment_curr_mxn)

        for field1, field2 in (('debit', 'credit'), ('credit', 'debit')):
            for partial in pay_rec_lines[f'matched_{field1}_ids']:
                payment_line = partial[f'{field2}_move_id']
                invoice_line = partial[f'{field1}_move_id']
                invoice_amount = partial[f'{field1}_amount_currency']
                exchange_move = invoice_line.full_reconcile_id.exchange_move_id
                invoice = invoice_line.move_id

                if not invoice.l10n_mx_edi_cfdi_request:
                    continue

                if exchange_move:
                    exchange_partial = invoice_line[f'matched_{field2}_ids'] \
                        .filtered(lambda x: x[
                                                f'{field2}_move_id'].move_id == exchange_move)
                    if exchange_partial:
                        invoice_amount += exchange_partial[
                            f'{field2}_amount_currency']

                if invoice_line.currency_id == payment_line.currency_id:
                    amount_paid_invoice_curr = invoice_amount
                    exchange_rate = None
                else:
                    amount_paid_invoice_comp_curr = payment_line.company_currency_id.round(
                        total_amount * (partial.amount / paid_amount_comp_curr))
                    invoice_rate = abs(invoice_line.amount_currency) / abs(
                        invoice_line.balance)
                    amount_paid_invoice_curr = invoice_line.currency_id.round(
                        partial.amount * invoice_rate)
                    exchange_rate = amount_paid_invoice_curr / amount_paid_invoice_comp_curr

                invoice_vals_list.append({
                    'invoice': invoice,
                    'exchange_rate': exchange_rate,
                    'payment_policy': invoice.l10n_mx_edi_payment_policy,
                    'number_of_payments': len(
                        invoice._get_reconciled_payments()) + len(
                        invoice._get_reconciled_statement_lines()),
                    'amount_paid': amount_paid_invoice_curr,
                    'amount_before_paid': min(
                        invoice.amount_residual + amount_paid_invoice_curr,
                        invoice.amount_total),
                    **self._l10n_mx_edi_get_serie_and_folio(invoice),
                })

        payment_method_code = move.l10n_mx_edi_payment_method_id.code
        is_payment_code_emitter_ok = payment_method_code in (
            '02', '03', '04', '05', '06', '28', '29', '99')
        is_payment_code_receiver_ok = payment_method_code in (
            '02', '03', '04', '05', '28', '29', '99')
        is_payment_code_bank_ok = payment_method_code in (
            '02', '03', '04', '28', '29', '99')

        partner_bank = move.partner_bank_id.bank_id
        if partner_bank.country and partner_bank.country.code != 'MX':
            partner_bank_vat = 'XEXX010101000'
        else:
            partner_bank_vat = partner_bank.l10n_mx_edi_vat

        payment_account_ord = re.sub(r'\s+', '', move.partner_bank_id.acc_number or '') or None
        payment_account_receiver = re.sub(r'\s+', '', move.journal_id.bank_account_id.acc_number or '') or None
        cfdi_values = {
            **self._l10n_mx_edi_get_common_cfdi_values(move),
            'invoice_vals_list': invoice_vals_list,
            'currency': currency,
            'amount': total_amount,
            'rate_payment_curr_mxn': rate_payment_curr_mxn,
            'emitter_vat_ord': is_payment_code_emitter_ok and partner_bank_vat,
            'bank_vat_ord': is_payment_code_bank_ok and partner_bank.name,
            'payment_account_ord': is_payment_code_emitter_ok and payment_account_ord,
            'receiver_vat_ord': is_payment_code_receiver_ok and move.journal_id.bank_account_id.bank_id.l10n_mx_edi_vat,
            'payment_account_receiver': is_payment_code_receiver_ok and payment_account_receiver,
            'cfdi_date': move.l10n_mx_edi_post_time.strftime('%Y-%m-%dT%H:%M:%S'),
        }
        to_zone = tz.gettz(self.env.context['tz'])
        converted_time = move.payment_id.x_studio_fecha_y_hora_de_pago.astimezone(
            to_zone)
        cfdi_values['cfdi_payment_date'] = converted_time.strftime(
            '%Y-%m-%dT%H:%M:%S')
        if cfdi_values['customer'].country_id.l10n_mx_edi_code != 'MEX':
            cfdi_values['customer_fiscal_residence'] = cfdi_values[
                'customer'].country_id.l10n_mx_edi_code
        else:
            cfdi_values['customer_fiscal_residence'] = None

        cfdi = self.env.ref('l10n_mx_edi.payment10')._render(cfdi_values)
        decoded_cfdi_values = move._l10n_mx_edi_decode_cfdi(cfdi_data=cfdi)
        cfdi_cadena_crypted = cfdi_values[
            'certificate'].sudo().get_encrypted_cadena(
            decoded_cfdi_values['cadena'])
        decoded_cfdi_values['cfdi_node'].attrib['Sello'] = cfdi_cadena_crypted

        return {
            'cfdi_str': etree.tostring(decoded_cfdi_values['cfdi_node'],
                                       pretty_print=True, xml_declaration=True,
                                       encoding='UTF-8'),
        }
