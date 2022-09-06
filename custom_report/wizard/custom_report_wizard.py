# -*- coding: utf-8 -*-
from odoo import fields, models
import io
from odoo.tools import date_utils
from datetime import date
from odoo.exceptions import UserError
import json

try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter


class ReportInheritAccountMove(models.Model):
    _inherit = 'account.move'
    payment_date = fields.Date()
    payment_amount = fields.Float()


class CustomReportWizard(models.TransientModel):
    _name = 'custom.report.wizard'
    report_detail = fields.Selection(
        [('no_invoice_line_detail', 'No Invoice Line Detail'),
         ('invoice_line_detail', 'Invoice Line Detail')],
        default="no_invoice_line_detail")

    report_type = fields.Selection([('all_invoices', 'All Invoices'), (
        'only_paid_invoices', 'Only Paid Invoices')],
                                   default="all_invoices")
    invoice_initial_date = fields.Date()
    invoice_final_date = fields.Date()
    payment_initial_date = fields.Date()
    payment_final_date = fields.Date()

    def print_xlsx(self):
        account_id = self.env["account.move"].search(
            [('state', '=', 'posted'), ('move_type', '=', 'out_invoice')])
        for widget_line in account_id:
            if widget_line.invoice_payments_widget != 'false':
                json_data = json.loads(widget_line.invoice_payments_widget)
                amount_sum = 0
                for content_line in json_data.get('content'):
                    amount_sum += content_line.get('amount')
                    amount_date = content_line.get('date')
                    widget_line.update(
                        {'payment_date': amount_date,
                         'payment_amount': amount_sum})
        line = flag = 0
        today = date.today()
        company = self.env['res.company'].browse(
            self._context.get('company_id')) or self.env.company
        currency_rates = self.env['res.currency'].search([])._get_rates(company,
                                                                        today)
        for i in currency_rates:
            if (self.env['res.currency'].search(
                    [('name', '=', 'MXN')]).id) == i:
                exchange_rate = currency_rates[i]
                flag = 1

        if flag != 1:
            raise UserError(
                "Please enable MXN currency for viewing proper exchange rate")

        # Query for all invoice

        query1 = """SELECT DISTINCT account_move.name as invoice_number,
                    account_move.id as move_id,
                    account_move.payment_state as payment_info,
                    account_move.invoice_partner_display_name as client_name,
                    account_move.invoice_date_due as invoice_date_due,
                    account_move.date as invoice_created_date,
                    account_move.amount_untaxed_signed as subtotal_amount,
                    account_move.amount_total_signed as total_amount,
                    res_currency.name as currency, 
                    res_partner.name as sales_person,
                    crm_team.name as sales_team,
                    account_move.payment_date as invoice_paid_date,
                    account_move.payment_amount as invoice_paid_amount
                    from account_move inner join res_currency on res_currency.id=account_move.currency_id
                    inner join res_currency_rate on res_currency_rate.currency_id=account_move.currency_id
                    inner join res_users on res_users.id=account_move.invoice_user_id
                    inner join res_partner on res_partner.id=res_users.partner_id
                    inner join crm_team on crm_team.id = account_move.team_id
                    where account_move.state='posted' and account_move.move_type='out_invoice'"""

        # combination of no invoice details line and all invoices

        if self.report_detail == 'no_invoice_line_detail' and self.report_type == 'all_invoices':
            line = 0
            if self.invoice_initial_date and self.invoice_final_date:
                self.env.cr.execute(
                    query1 + "  and account_move.company_id=%(company_id)s and account_move.date >= %(invoice_initial_date)s and account_move.date <= %(invoice_final_date)s",
                    {"invoice_initial_date": self.invoice_initial_date,
                     "invoice_final_date": self.invoice_final_date,
                     'company_id': self.env.company.id})
                excel_results = self.env.cr.dictfetchall()
            elif self.invoice_initial_date:
                self.env.cr.execute(
                    query1 + " and account_move.company_id=%(company_id)s and account_move.date >= %(invoice_initial_date)s and account_move.date <= %(invoice_final_date)s",
                    {"invoice_initial_date": self.invoice_initial_date,
                     "invoice_final_date": today,
                     'company_id': self.env.company.id})
                excel_results = self.env.cr.dictfetchall()
            elif self.invoice_final_date:
                self.env.cr.execute(
                    query1 + " and account_move.company_id=%(company_id)s and account_move.date <= %(invoice_final_date)s",
                    {"invoice_final_date": self.invoice_final_date,
                     'company_id': self.env.company.id})
                excel_results = self.env.cr.dictfetchall()
            else:
                self.env.cr.execute(
                    query1 + " and account_move.company_id=%(company_id)s",
                    {'company_id': self.env.company.id})
                excel_results = self.env.cr.dictfetchall()

        # combination of invoice line details and all invoices

        if self.report_detail == 'invoice_line_detail' and self.report_type == 'all_invoices':
            line = 1
            if self.invoice_initial_date and self.invoice_final_date:
                self.env.cr.execute(
                    query1 + " and account_move.company_id=%(company_id)s and account_move.date >= %(invoice_initial_date)s and account_move.date <= %(invoice_final_date)s",
                    {"invoice_initial_date": self.invoice_initial_date,
                     "invoice_final_date": self.invoice_final_date,
                     'company_id': self.env.company.id})
                excel_results = self.env.cr.dictfetchall()
            elif self.invoice_initial_date:
                self.env.cr.execute(
                    query1 + " and account_move.company_id=%(company_id)s and account_move.date >= %(invoice_initial_date)s and account_move.date <= %(invoice_final_date)s",
                    {"invoice_initial_date": self.invoice_initial_date,
                     "invoice_final_date": today,
                     'company_id': self.env.company.id})
                excel_results = self.env.cr.dictfetchall()
            elif self.invoice_final_date:
                self.env.cr.execute(
                    query1 + " and account_move.company_id=%(company_id)s and account_move.date <= %(invoice_final_date)s",
                    {"invoice_final_date": self.invoice_final_date,
                     'company_id': self.env.company.id})
                excel_results = self.env.cr.dictfetchall()
            else:
                self.env.cr.execute(
                    query1 + " and account_move.company_id=%(company_id)s",
                    {'company_id': self.env.company.id})
                excel_results = self.env.cr.dictfetchall()

        # combination of no invoice line details and paid invoices only

        if self.report_detail == 'no_invoice_line_detail' and self.report_type == 'only_paid_invoices':
            line = 0
            if self.payment_initial_date and self.payment_final_date:
                if self.invoice_initial_date and self.invoice_final_date:
                    self.env.cr.execute(
                        query1 + " and account_move.company_id=%(company_id)s and account_move.date >= %(invoice_initial_date)s and account_move.date <= %(invoice_final_date)s and account_move.payment_date >= %(payment_initial_date)s and account_move.payment_date <= %(payment_final_date)s and account_move.payment_state in('paid','in_payment')",
                        {"invoice_initial_date": self.invoice_initial_date,
                         "invoice_final_date": self.invoice_final_date,
                         "payment_initial_date": self.payment_initial_date,
                         "payment_final_date": self.payment_final_date,
                         'company_id': self.env.company.id})
                    excel_results = self.env.cr.dictfetchall()

                elif self.invoice_initial_date:
                    self.env.cr.execute(
                        query1 + " and account_move.company_id=%(company_id)s and account_move.date >= %(invoice_initial_date)s and account_move.date <= %(invoice_final_date)s and account_move.payment_date >= %(payment_initial_date)s and account_move.payment_date <= %(payment_final_date)s and account_move.payment_state in('paid','in_payment')",
                        {"invoice_initial_date": self.invoice_initial_date,
                         "invoice_final_date": today,
                         "payment_initial_date": self.payment_initial_date,
                         "payment_final_date": self.payment_final_date,
                         'company_id': self.env.company.id})
                    excel_results = self.env.cr.dictfetchall()

                elif self.invoice_final_date:
                    self.env.cr.execute(
                        query1 + " and account_move.company_id=%(company_id)s and account_move.date <= %(invoice_final_date)s and account_move.payment_date >= %(payment_initial_date)s and account_move.payment_date <= %(payment_final_date)s and account_move.payment_state in('paid','in_payment')",
                        {"invoice_final_date": self.invoice_final_date,
                         "payment_initial_date": self.payment_initial_date,
                         "payment_final_date": self.payment_final_date,
                         'company_id': self.env.company.id})
                    excel_results = self.env.cr.dictfetchall()

                else:
                    self.env.cr.execute(
                        query1 + " and account_move.company_id=%(company_id)s and account_move.payment_state in('paid','in_payment') and account_move.payment_date >= %(payment_initial_date)s and account_move.payment_date <= %(payment_final_date)s",
                        {'company_id': self.env.company.id,
                         "payment_initial_date": self.payment_initial_date,
                         "payment_final_date": self.payment_final_date
                         })
                    excel_results = self.env.cr.dictfetchall()

            elif self.payment_initial_date:
                if self.invoice_initial_date and self.invoice_final_date:
                    self.env.cr.execute(
                        query1 + " and account_move.company_id=%(company_id)s and account_move.date >= %(invoice_initial_date)s and account_move.date <= %(invoice_final_date)s and account_move.payment_date >= %(payment_initial_date)s and account_move.payment_date <= %(payment_final_date)s and account_move.payment_state in('paid','in_payment')",
                        {"invoice_initial_date": self.invoice_initial_date,
                         "invoice_final_date": self.invoice_final_date,
                         "payment_initial_date": self.payment_initial_date,
                         "payment_final_date": today,
                         'company_id': self.env.company.id})
                    excel_results = self.env.cr.dictfetchall()
                elif self.invoice_initial_date:
                    self.env.cr.execute(
                        query1 + " and account_move.company_id=%(company_id)s and account_move.date >= %(invoice_initial_date)s and account_move.date <= %(invoice_final_date)s and account_move.payment_date >= %(payment_initial_date)s and account_move.payment_date <= %(payment_final_date)s and account_move.payment_state in('paid','in_payment')",
                        {"invoice_initial_date": self.invoice_initial_date,
                         "invoice_final_date": today,
                         "payment_initial_date": self.payment_initial_date,
                         "payment_final_date": today,
                         'company_id': self.env.company.id})
                    excel_results = self.env.cr.dictfetchall()
                elif self.invoice_final_date:
                    self.env.cr.execute(
                        query1 + " and account_move.company_id=%(company_id)s and account_move.date <= %(invoice_final_date)s and account_move.payment_date >= %(payment_initial_date)s and account_move.payment_date <= %(payment_final_date)s and account_move.payment_state in('paid','in_payment')",
                        {"invoice_final_date": self.invoice_final_date,
                         "payment_initial_date": self.payment_initial_date,
                         "payment_final_date": today,
                         'company_id': self.env.company.id})
                    excel_results = self.env.cr.dictfetchall()
                else:
                    self.env.cr.execute(
                        query1 + " and account_move.company_id=%(company_id)s and account_move.payment_state in('paid','in_payment') and account_move.payment_date >= %(payment_initial_date)s and account_move.payment_date <= %(payment_final_date)s",
                        {'company_id': self.env.company.id,
                         "payment_initial_date": self.payment_initial_date,
                         "payment_final_date": today
                         })
                    excel_results = self.env.cr.dictfetchall()

            elif self.payment_final_date:
                if self.invoice_initial_date and self.invoice_final_date:
                    self.env.cr.execute(
                        query1 + " and account_move.company_id=%(company_id)s and account_move.date >= %(invoice_initial_date)s and account_move.date <= %(invoice_final_date)s and account_move.payment_date <= %(payment_final_date)s and account_move.payment_state in('paid','in_payment')",
                        {"invoice_initial_date": self.invoice_initial_date,
                         "invoice_final_date": self.invoice_final_date,
                         "payment_final_date": self.payment_final_date,
                         'company_id': self.env.company.id})
                    excel_results = self.env.cr.dictfetchall()
                elif self.invoice_initial_date:
                    self.env.cr.execute(
                        query1 + " and account_move.company_id=%(company_id)s and account_move.date >= %(invoice_initial_date)s and account_move.date <= %(invoice_final_date)s and account_move.payment_date <= %(payment_final_date)s and account_move.payment_state in('paid','in_payment')",
                        {"invoice_initial_date": self.invoice_initial_date,
                         "invoice_final_date": today,
                         "payment_final_date": self.payment_final_date,
                         'company_id': self.env.company.id})
                    excel_results = self.env.cr.dictfetchall()
                elif self.invoice_final_date:
                    self.env.cr.execute(
                        query1 + " and account_move.company_id=%(company_id)s and account_move.date <= %(invoice_final_date)s and account_move.payment_date <= %(payment_final_date)s and account_move.payment_state in('paid','in_payment')",
                        {"invoice_final_date": self.invoice_final_date,
                         "payment_final_date": self.payment_final_date,
                         'company_id': self.env.company.id})
                    excel_results = self.env.cr.dictfetchall()
                else:
                    self.env.cr.execute(
                        query1 + " and account_move.company_id=%(company_id)s and account_move.payment_state in('paid','in_payment') and account_move.payment_date <= %(payment_final_date)s",
                        {'company_id': self.env.company.id,
                         "payment_final_date": self.payment_final_date
                         })
                    excel_results = self.env.cr.dictfetchall()

            else:
                if self.invoice_initial_date and self.invoice_final_date:
                    self.env.cr.execute(
                        query1 + " and account_move.company_id=%(company_id)s and account_move.date >= %(invoice_initial_date)s and account_move.date <= %(invoice_final_date)s and account_move.payment_state in('paid','in_payment')",
                        {"invoice_initial_date": self.invoice_initial_date,
                         "invoice_final_date": self.invoice_final_date,
                         'company_id': self.env.company.id})
                    excel_results = self.env.cr.dictfetchall()

                elif self.invoice_initial_date:
                    self.env.cr.execute(
                        query1 + " and account_move.company_id=%(company_id)s and account_move.date >= %(invoice_initial_date)s and account_move.date <= %(invoice_final_date)s and account_move.payment_state in('paid','in_payment')",
                        {"invoice_initial_date": self.invoice_initial_date,
                         "invoice_final_date": today,
                         'company_id': self.env.company.id})
                    excel_results = self.env.cr.dictfetchall()

                elif self.invoice_final_date:
                    self.env.cr.execute(
                        query1 + " and account_move.company_id=%(company_id)s and account_move.date <= %(invoice_final_date)s and account_move.payment_state in('paid','in_payment')",
                        {"invoice_final_date": self.invoice_final_date,
                         'company_id': self.env.company.id})
                    excel_results = self.env.cr.dictfetchall()

                else:
                    self.env.cr.execute(
                        query1 + " and account_move.company_id=%(company_id)s and account_move.payment_state in('paid','in_payment')",
                        {'company_id': self.env.company.id})
                    excel_results = self.env.cr.dictfetchall()

        # combination of invoice line details and paid invoices only

        if self.report_detail == 'invoice_line_detail' and self.report_type == 'only_paid_invoices':
            line = 1
            if self.payment_initial_date and self.payment_final_date:
                if self.invoice_initial_date and self.invoice_final_date:
                    self.env.cr.execute(
                        query1 + " and account_move.company_id=%(company_id)s and account_move.date >= %(invoice_initial_date)s and account_move.date <= %(invoice_final_date)s and account_move.payment_date >= %(payment_initial_date)s and account_move.payment_date <= %(payment_final_date)s and account_move.payment_state in('paid','in_payment')",
                        {"invoice_initial_date": self.invoice_initial_date,
                         "invoice_final_date": self.invoice_final_date,
                         "payment_initial_date": self.payment_initial_date,
                         "payment_final_date": self.payment_final_date,
                         'company_id': self.env.company.id})
                    excel_results = self.env.cr.dictfetchall()

                elif self.invoice_initial_date:
                    self.env.cr.execute(
                        query1 + " and account_move.company_id=%(company_id)s and account_move.date >= %(invoice_initial_date)s and account_move.date <= %(invoice_final_date)s and account_move.payment_date >= %(payment_initial_date)s and account_move.payment_date <= %(payment_final_date)s and account_move.payment_state in('paid','in_payment')",
                        {"invoice_initial_date": self.invoice_initial_date,
                         "invoice_final_date": today,
                         "payment_initial_date": self.payment_initial_date,
                         "payment_final_date": self.payment_final_date,
                         'company_id': self.env.company.id})
                    excel_results = self.env.cr.dictfetchall()

                elif self.invoice_final_date:
                    self.env.cr.execute(
                        query1 + " and account_move.company_id=%(company_id)s and account_move.date <= %(invoice_final_date)s and account_move.payment_date >= %(payment_initial_date)s and account_move.payment_date <= %(payment_final_date)s and account_move.payment_state in('paid','in_payment')",
                        {"invoice_final_date": self.invoice_final_date,
                         "payment_initial_date": self.payment_initial_date,
                         "payment_final_date": self.payment_final_date,
                         'company_id': self.env.company.id})
                    excel_results = self.env.cr.dictfetchall()

                else:
                    self.env.cr.execute(
                        query1 + " and account_move.company_id=%(company_id)s and account_move.payment_state in('paid','in_payment') and account_move.payment_date >= %(payment_initial_date)s and account_move.payment_date <= %(payment_final_date)s",
                        {'company_id': self.env.company.id,
                         "payment_initial_date": self.payment_initial_date,
                         "payment_final_date": self.payment_final_date
                         })
                    excel_results = self.env.cr.dictfetchall()

            elif self.payment_initial_date:
                if self.invoice_initial_date and self.invoice_final_date:
                    self.env.cr.execute(
                        query1 + " and account_move.company_id=%(company_id)s and account_move.date >= %(invoice_initial_date)s and account_move.date <= %(invoice_final_date)s and account_move.payment_date >= %(payment_initial_date)s and account_move.payment_date <= %(payment_final_date)s and account_move.payment_state in('paid','in_payment')",
                        {"invoice_initial_date": self.invoice_initial_date,
                         "invoice_final_date": self.invoice_final_date,
                         "payment_initial_date": self.payment_initial_date,
                         "payment_final_date": today,
                         'company_id': self.env.company.id})
                    excel_results = self.env.cr.dictfetchall()
                elif self.invoice_initial_date:
                    self.env.cr.execute(
                        query1 + " and account_move.company_id=%(company_id)s and account_move.date >= %(invoice_initial_date)s and account_move.date <= %(invoice_final_date)s and account_move.payment_date >= %(payment_initial_date)s and account_move.payment_date <= %(payment_final_date)s and account_move.payment_state in('paid','in_payment')",
                        {"invoice_initial_date": self.invoice_initial_date,
                         "invoice_final_date": today,
                         "payment_initial_date": self.payment_initial_date,
                         "payment_final_date": today,
                         'company_id': self.env.company.id})
                    excel_results = self.env.cr.dictfetchall()
                elif self.invoice_final_date:
                    self.env.cr.execute(
                        query1 + " and account_move.company_id=%(company_id)s and account_move.date <= %(invoice_final_date)s and account_move.payment_date >= %(payment_initial_date)s and account_move.payment_date <= %(payment_final_date)s and account_move.payment_state in('paid','in_payment')",
                        {"invoice_final_date": self.invoice_final_date,
                         "payment_initial_date": self.payment_initial_date,
                         "payment_final_date": today,
                         'company_id': self.env.company.id})
                    excel_results = self.env.cr.dictfetchall()
                else:
                    self.env.cr.execute(
                        query1 + " and account_move.company_id=%(company_id)s and account_move.payment_state in('paid','in_payment') and account_move.payment_date >= %(payment_initial_date)s and account_move.payment_date <= %(payment_final_date)s",
                        {'company_id': self.env.company.id,
                         "payment_initial_date": self.payment_initial_date,
                         "payment_final_date": today
                         })
                    excel_results = self.env.cr.dictfetchall()

            elif self.payment_final_date:
                if self.invoice_initial_date and self.invoice_final_date:
                    self.env.cr.execute(
                        query1 + " and account_move.company_id=%(company_id)s and account_move.date >= %(invoice_initial_date)s and account_move.date <= %(invoice_final_date)s and account_move.payment_date <= %(payment_final_date)s and account_move.payment_state in('paid','in_payment')",
                        {"invoice_initial_date": self.invoice_initial_date,
                         "invoice_final_date": self.invoice_final_date,
                         "payment_final_date": self.payment_final_date,
                         'company_id': self.env.company.id})
                    excel_results = self.env.cr.dictfetchall()
                elif self.invoice_initial_date:
                    self.env.cr.execute(
                        query1 + " and account_move.company_id=%(company_id)s and account_move.date >= %(invoice_initial_date)s and account_move.date <= %(invoice_final_date)s and account_move.payment_date <= %(payment_final_date)s and account_move.payment_state in('paid','in_payment')",
                        {"invoice_initial_date": self.invoice_initial_date,
                         "invoice_final_date": today,
                         "payment_final_date": self.payment_final_date,
                         'company_id': self.env.company.id})
                    excel_results = self.env.cr.dictfetchall()
                elif self.invoice_final_date:
                    self.env.cr.execute(
                        query1 + " and account_move.company_id=%(company_id)s and account_move.date <= %(invoice_final_date)s and account_move.payment_date <= %(payment_final_date)s and account_move.payment_state in('paid','in_payment')",
                        {"invoice_final_date": self.invoice_final_date,
                         "payment_final_date": self.payment_final_date,
                         'company_id': self.env.company.id})
                    excel_results = self.env.cr.dictfetchall()
                else:
                    self.env.cr.execute(
                        query1 + " and account_move.company_id=%(company_id)s and account_move.payment_state in('paid','in_payment') and account_move.payment_date <= %(payment_final_date)s",
                        {'company_id': self.env.company.id,
                         "payment_final_date": self.payment_final_date
                         })
                    excel_results = self.env.cr.dictfetchall()

            else:
                if self.invoice_initial_date and self.invoice_final_date:
                    self.env.cr.execute(
                        query1 + " and account_move.company_id=%(company_id)s and account_move.date >= %(invoice_initial_date)s and account_move.date <= %(invoice_final_date)s and account_move.payment_state in('paid','in_payment')",
                        {"invoice_initial_date": self.invoice_initial_date,
                         "invoice_final_date": self.invoice_final_date,
                         'company_id': self.env.company.id})
                    excel_results = self.env.cr.dictfetchall()

                elif self.invoice_initial_date:
                    self.env.cr.execute(
                        query1 + " and account_move.company_id=%(company_id)s and account_move.date >= %(invoice_initial_date)s and account_move.date <= %(invoice_final_date)s and account_move.payment_state in('paid','in_payment')",
                        {"invoice_initial_date": self.invoice_initial_date,
                         "invoice_final_date": today,
                         'company_id': self.env.company.id})
                    excel_results = self.env.cr.dictfetchall()

                elif self.invoice_final_date:
                    self.env.cr.execute(
                        query1 + " and account_move.company_id=%(company_id)s and account_move.date <= %(invoice_final_date)s and account_move.payment_state in('paid','in_payment')",
                        {"invoice_final_date": self.invoice_final_date,
                         'company_id': self.env.company.id})
                    excel_results = self.env.cr.dictfetchall()

                else:
                    self.env.cr.execute(
                        query1 + " and account_move.company_id=%(company_id)s and account_move.payment_state in('paid','in_payment')",
                        {'company_id': self.env.company.id})
                    excel_results = self.env.cr.dictfetchall()

        data = {
            'excel_result': excel_results,
            'todate': today,
            'responcible': self.env.user.name,
            'line': line,
            'exchange_rate': exchange_rate
        }

        return {
            'type': 'ir.actions.report',
            'data': {'model': 'custom.report.wizard',
                     'options': json.dumps(data,
                                           default=date_utils.json_default),
                     'output_format': 'xlsx',
                     'report_name': 'Project Report',
                     },
            'report_type': 'xlsx'
        }

    def get_xlsx_report(self, data, response):

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet()
        sheet.set_row(0, 30)
        sheet.set_column(0, 0, 5)
        sheet.set_column(1, 1, 12)
        sheet.set_column(2, 2, 16)
        sheet.set_column(3, 3, 13)
        sheet.set_column(4, 4, 15)
        sheet.set_column(5, 5, 10)
        sheet.set_column(6, 6, 9)
        sheet.set_column(7, 7, 12)
        sheet.set_column(8, 8, 14)
        sheet.set_column(9, 9, 10)
        sheet.set_column(10, 10, 12)
        sheet.set_column(11, 11, 8)
        sheet.set_column(12, 12, 12)
        sheet.set_column(13, 13, 14)
        sheet.set_column(14, 14, 15)

        head = workbook.add_format(
            {'align': 'vcenter', 'valign': 'left', 'bold': True,
             'font_color': '#666666', 'font_name': 'times new roman',
             'font_size': '20px'})

        date_format = workbook.add_format(
            {'align': 'vcenter', 'bold': True,
             'font_color': '#666666', 'font_name': 'times new roman',
             'font_size': '12px'})

        date_content = workbook.add_format(
            {'align': 'vcenter', 'valign': 'left', 'bold': True,
             'font_color': '#666666', 'font_name': 'times new roman',
             'font_size': '12px'})

        sub_head = workbook.add_format(
            {'align': 'vcenter', 'valign': 'left', 'font_size': '10px',
             'font_color': 'white',
             'bg_color': '#666666',
             'border': True})
        sub_head2 = workbook.add_format(
            {'align': 'vcenter', 'valign': 'left', 'font_size': '10px',
             'font_color': 'white',
             'bg_color': '#999999',
             'border': True})

        cell_content = workbook.add_format(
            {'align': 'left', 'border': True, 'font_size': '10px'})

        # Headers
        sheet.merge_range('A1:D1', 'Custom Monthly Sales Report', head)

        # Date Field
        if self.env.ref('base.main_company').currency_id.name != 'MXN':
            sheet.write('J1', 'Date', date_format)
            sheet.write('K1', data['todate'], date_content)
        else:
            sheet.write('J1', 'Date', date_format)
            sheet.write('K1', data['todate'], date_content)

        # sub titles
        sheet.write('A3', 'Sl No', sub_head)
        sheet.write('B3', 'Invoice No', sub_head)
        sheet.write('C3', 'Invoice Created date', sub_head)
        sheet.write('D3', 'Invoice Due Date', sub_head)
        sheet.write('E3', 'Invoice Paid Date', sub_head)
        sheet.write('F3', 'Client Name', sub_head)
        sheet.write('G3', 'Sales Team', sub_head)
        sheet.write('H3', 'Sales Man', sub_head)
        sheet.write('I3', 'Sub Total', sub_head)
        sheet.write('J3', 'Total', sub_head)
        sheet.write('K3', 'Paid Amount', sub_head)
        if self.env.ref('base.main_company').currency_id.name != 'MXN':
            sheet.write('L3', 'Currency', sub_head)
            sheet.write('M3', 'Exchange Rate', sub_head)
            sheet.write('N3', 'Total Amount MXN', sub_head)
            sheet.write('O3', 'Paid Amount MXN', sub_head)

        row_number = 3
        column_number = 0
        count = 1
        for i in data['excel_result']:
            sheet.write(row_number, column_number, count, cell_content)
            sheet.write(row_number, column_number + 1, i['invoice_number'],
                        cell_content)
            sheet.write(row_number, column_number + 2,
                        i['invoice_created_date'], cell_content)
            sheet.write(row_number, column_number + 3, i['invoice_date_due'],
                        cell_content)
            move_line_id = self.env['account.move'].browse(i['move_id'])
            if i['invoice_paid_date']:
                sheet.write(row_number, column_number + 4,
                            i['invoice_paid_date'],
                            cell_content)
                sheet.write(row_number, column_number + 10,
                            i['invoice_paid_amount'],
                            cell_content)
            else:
                sheet.write(row_number, column_number + 4, 'Not paid',
                            cell_content)
                sheet.write(row_number, column_number + 10, 0, cell_content)
            sheet.write(row_number, column_number + 5, i['client_name'],
                        cell_content)
            sheet.write(row_number, column_number + 6, i['sales_team'],
                        cell_content)
            sheet.write(row_number, column_number + 7, i['sales_person'],
                        cell_content)
            sheet.write(row_number, column_number + 8, i['subtotal_amount'],
                        cell_content)
            sheet.write(row_number, column_number + 9, i['total_amount'],
                        cell_content)
            if self.env.ref('base.main_company').currency_id.name != 'MXN':
                sheet.write(row_number, column_number + 11, i['currency'],
                            cell_content)
                sheet.write(row_number, column_number + 12,
                            data['exchange_rate'],
                            cell_content)
                sheet.write(row_number, column_number + 13,
                            (data['exchange_rate'] * i['total_amount']),
                            cell_content)
                if i['invoice_paid_date']:
                    sheet.write(row_number, column_number + 14,
                                (data['exchange_rate'] * i[
                                    'invoice_paid_amount']),
                                cell_content)
                else:
                    sheet.write(row_number, column_number + 14,
                                (data['exchange_rate'] * 0),
                                cell_content)

            row_number += 1
            count += 1
            if data['line'] == 1:
                column_numbers = 0
                sheet.write(row_number, column_numbers, ' ', cell_content)
                sheet.write(row_number, column_numbers + 1, 'Sl No', sub_head2)
                sheet.write(row_number, column_numbers + 2, 'Product',
                            sub_head2)
                sheet.write(row_number, column_numbers + 3, 'Quantity',
                            sub_head2)
                sheet.write(row_number, column_numbers + 4,
                            'Unit of Measurement', sub_head2)
                sheet.write(row_number, column_numbers + 5, 'Discount',
                            sub_head2)
                sheet.write(row_number, column_numbers + 6, 'Sale Cost',
                            sub_head2)
                sheet.write(row_number, column_numbers + 7, 'Sub Total',
                            sub_head2)
                sheet.write(row_number, column_numbers + 8, 'Total',
                            sub_head2)
                if self.env.ref('base.main_company').currency_id.name != 'MXN':
                    sheet.write(row_number, column_numbers + 9,
                                'Total Amount MXN',
                                sub_head2)
                else:
                    sheet.write(row_number, column_numbers + 9, ' ',
                                cell_content)
                sheet.write(row_number, column_numbers + 10, ' ',
                            cell_content)
                if self.env.ref('base.main_company').currency_id.name != 'MXN':
                    sheet.write(row_number, column_numbers + 11, ' ',
                                cell_content)
                    sheet.write(row_number, column_numbers + 12, ' ',
                                cell_content)
                    sheet.write(row_number, column_numbers + 13, ' ',
                                cell_content)
                    sheet.write(row_number, column_numbers + 14, ' ',
                                cell_content)
                row_number += 1
                self.env.cr.execute(""" SELECT account_move_line.quantity as line_quantity,
                                        ir_property.value_float as standard_price, 
                                        account_move_line.discount as line_discount,
                                        account_move_line.price_subtotal as line_subtotal,
                                        account_move_line.price_total as line_total,
                                        product_template.name as line_product,
                                        uom_uom.name as line_unit
                                        from account_move_line inner join product_product on product_product.id = account_move_line.product_id
                                        inner join product_template on product_template.id=product_product.product_tmpl_id
                                        inner join ir_property on ir_property.res_id = 'product.product,' || product_product.id
                                        inner join uom_uom on uom_uom.id=product_uom_id 
                                        inner join account_account on account_move_line.account_id=account_account.id
                                        where account_move_line.move_id=%(invoice_id)s and account_account.internal_group in('income') 
                                        and product_product.product_tmpl_id = product_template.id """,
                                    {"invoice_id": i['move_id']})
                line_result = self.env.cr.dictfetchall()
                line_count = 1
                for j in line_result:
                    sheet.write(row_number, column_numbers, '',
                                cell_content)
                    sheet.write(row_number, column_numbers + 1, line_count,
                                cell_content)
                    sheet.write(row_number, column_numbers + 2,
                                j['line_product'], cell_content)
                    sheet.write(row_number, column_numbers + 3,
                                j['line_quantity'], cell_content)
                    sheet.write(row_number, column_numbers + 4, j['line_unit'],
                                cell_content)
                    sheet.write(row_number, column_numbers + 5,
                                j['line_discount'], cell_content)
                    sheet.write(row_number, column_numbers + 6,
                                j['standard_price'], cell_content)
                    sheet.write(row_number, column_numbers + 7,
                                j['line_subtotal'], cell_content)
                    sheet.write(row_number, column_numbers + 8, j['line_total'],
                                cell_content)
                    if self.env.ref(
                            'base.main_company').currency_id.name != 'MXN':
                        sheet.write(row_number, column_numbers + 9,
                                    (data['exchange_rate'] * j['line_total']),
                                    cell_content)
                    else:
                        sheet.write(row_number, column_numbers + 9,
                                    '', cell_content)
                    sheet.write(row_number, column_numbers + 10,
                                '', cell_content)
                    if self.env.ref(
                            'base.main_company').currency_id.name != 'MXN':
                        sheet.write(row_number, column_numbers + 11,
                                    '', cell_content)
                        sheet.write(row_number, column_numbers + 12,
                                    '', cell_content)
                        sheet.write(row_number, column_numbers + 13,
                                    '', cell_content)
                        sheet.write(row_number, column_numbers + 14,
                                    '', cell_content)
                    row_number += 1
                    line_count += 1

        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()
