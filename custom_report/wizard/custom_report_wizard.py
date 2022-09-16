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

        query2 = """SELECT DISTINCT account_move.name as invoice_number,
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
                    account_move.payment_amount as invoice_paid_amount,
                    account_move_line.quantity as line_quantity,
                    ir_property.value_float as standard_price, 
                    account_move_line.discount as line_discount,
                    account_move_line.price_subtotal as line_subtotal,
                    product_template.name as line_product
                    from account_move inner join res_currency on res_currency.id=account_move.currency_id
                    inner join res_currency_rate on res_currency_rate.currency_id=account_move.currency_id
                    inner join res_users on res_users.id=account_move.invoice_user_id
                    inner join res_partner on res_partner.id=res_users.partner_id
                    inner join crm_team on crm_team.id = account_move.team_id
                    left join  account_move_line on account_move.id=account_move_line.move_id
                    inner join product_product on product_product.id = account_move_line.product_id
                    inner join product_template on product_template.id=product_product.product_tmpl_id
                    inner join ir_property on ir_property.res_id = 'product.product,' || product_product.id
                    inner join account_account on account_move_line.account_id=account_account.id
                    where account_account.internal_group in('income') 
                    and product_product.product_tmpl_id = product_template.id 
                    and account_move.state='posted' and account_move.move_type='out_invoice'"""

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
                    query2 + " and account_move.company_id=%(company_id)s and account_move.date >= %(invoice_initial_date)s and account_move.date <= %(invoice_final_date)s order by account_move.id",
                    {"invoice_initial_date": self.invoice_initial_date,
                     "invoice_final_date": self.invoice_final_date,
                     'company_id': self.env.company.id})
                excel_results = self.env.cr.dictfetchall()
            elif self.invoice_initial_date:
                self.env.cr.execute(
                    query2 + " and account_move.company_id=%(company_id)s and account_move.date >= %(invoice_initial_date)s and account_move.date <= %(invoice_final_date)s order by account_move.id",
                    {"invoice_initial_date": self.invoice_initial_date,
                     "invoice_final_date": today,
                     'company_id': self.env.company.id})
                excel_results = self.env.cr.dictfetchall()
            elif self.invoice_final_date:
                self.env.cr.execute(
                    query2 + " and account_move.company_id=%(company_id)s and account_move.date <= %(invoice_final_date)s order by account_move.id",
                    {"invoice_final_date": self.invoice_final_date,
                     'company_id': self.env.company.id})
                excel_results = self.env.cr.dictfetchall()
            else:
                self.env.cr.execute(
                    query2 + " and account_move.company_id=%(company_id)s order by account_move.id",
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
                        query2 + " and account_move.company_id=%(company_id)s and account_move.date >= %(invoice_initial_date)s and account_move.date <= %(invoice_final_date)s and account_move.payment_date >= %(payment_initial_date)s and account_move.payment_date <= %(payment_final_date)s and account_move.payment_state in('paid','in_payment') order by account_move.id",
                        {"invoice_initial_date": self.invoice_initial_date,
                         "invoice_final_date": self.invoice_final_date,
                         "payment_initial_date": self.payment_initial_date,
                         "payment_final_date": self.payment_final_date,
                         'company_id': self.env.company.id})
                    excel_results = self.env.cr.dictfetchall()

                elif self.invoice_initial_date:
                    self.env.cr.execute(
                        query2 + " and account_move.company_id=%(company_id)s and account_move.date >= %(invoice_initial_date)s and account_move.date <= %(invoice_final_date)s and account_move.payment_date >= %(payment_initial_date)s and account_move.payment_date <= %(payment_final_date)s and account_move.payment_state in('paid','in_payment') order by account_move.id",
                        {"invoice_initial_date": self.invoice_initial_date,
                         "invoice_final_date": today,
                         "payment_initial_date": self.payment_initial_date,
                         "payment_final_date": self.payment_final_date,
                         'company_id': self.env.company.id})
                    excel_results = self.env.cr.dictfetchall()

                elif self.invoice_final_date:
                    self.env.cr.execute(
                        query2 + " and account_move.company_id=%(company_id)s and account_move.date <= %(invoice_final_date)s and account_move.payment_date >= %(payment_initial_date)s and account_move.payment_date <= %(payment_final_date)s and account_move.payment_state in('paid','in_payment') order by account_move.id",
                        {"invoice_final_date": self.invoice_final_date,
                         "payment_initial_date": self.payment_initial_date,
                         "payment_final_date": self.payment_final_date,
                         'company_id': self.env.company.id})
                    excel_results = self.env.cr.dictfetchall()

                else:
                    self.env.cr.execute(
                        query2 + " and account_move.company_id=%(company_id)s and account_move.payment_state in('paid','in_payment') and account_move.payment_date >= %(payment_initial_date)s and account_move.payment_date <= %(payment_final_date)s order by account_move.id",
                        {'company_id': self.env.company.id,
                         "payment_initial_date": self.payment_initial_date,
                         "payment_final_date": self.payment_final_date
                         })
                    excel_results = self.env.cr.dictfetchall()

            elif self.payment_initial_date:
                if self.invoice_initial_date and self.invoice_final_date:
                    self.env.cr.execute(
                        query2 + " and account_move.company_id=%(company_id)s and account_move.date >= %(invoice_initial_date)s and account_move.date <= %(invoice_final_date)s and account_move.payment_date >= %(payment_initial_date)s and account_move.payment_date <= %(payment_final_date)s and account_move.payment_state in('paid','in_payment') order by account_move.id",
                        {"invoice_initial_date": self.invoice_initial_date,
                         "invoice_final_date": self.invoice_final_date,
                         "payment_initial_date": self.payment_initial_date,
                         "payment_final_date": today,
                         'company_id': self.env.company.id})
                    excel_results = self.env.cr.dictfetchall()
                elif self.invoice_initial_date:
                    self.env.cr.execute(
                        query2 + " and account_move.company_id=%(company_id)s and account_move.date >= %(invoice_initial_date)s and account_move.date <= %(invoice_final_date)s and account_move.payment_date >= %(payment_initial_date)s and account_move.payment_date <= %(payment_final_date)s and account_move.payment_state in('paid','in_payment') order by account_move.id",
                        {"invoice_initial_date": self.invoice_initial_date,
                         "invoice_final_date": today,
                         "payment_initial_date": self.payment_initial_date,
                         "payment_final_date": today,
                         'company_id': self.env.company.id})
                    excel_results = self.env.cr.dictfetchall()
                elif self.invoice_final_date:
                    self.env.cr.execute(
                        query2 + " and account_move.company_id=%(company_id)s and account_move.date <= %(invoice_final_date)s and account_move.payment_date >= %(payment_initial_date)s and account_move.payment_date <= %(payment_final_date)s and account_move.payment_state in('paid','in_payment') order by account_move.id",
                        {"invoice_final_date": self.invoice_final_date,
                         "payment_initial_date": self.payment_initial_date,
                         "payment_final_date": today,
                         'company_id': self.env.company.id})
                    excel_results = self.env.cr.dictfetchall()
                else:
                    self.env.cr.execute(
                        query2 + " and account_move.company_id=%(company_id)s and account_move.payment_state in('paid','in_payment') and account_move.payment_date >= %(payment_initial_date)s and account_move.payment_date <= %(payment_final_date)s order by account_move.id",
                        {'company_id': self.env.company.id,
                         "payment_initial_date": self.payment_initial_date,
                         "payment_final_date": today
                         })
                    excel_results = self.env.cr.dictfetchall()

            elif self.payment_final_date:
                if self.invoice_initial_date and self.invoice_final_date:
                    self.env.cr.execute(
                        query2 + " and account_move.company_id=%(company_id)s and account_move.date >= %(invoice_initial_date)s and account_move.date <= %(invoice_final_date)s and account_move.payment_date <= %(payment_final_date)s and account_move.payment_state in('paid','in_payment') order by account_move.id",
                        {"invoice_initial_date": self.invoice_initial_date,
                         "invoice_final_date": self.invoice_final_date,
                         "payment_final_date": self.payment_final_date,
                         'company_id': self.env.company.id})
                    excel_results = self.env.cr.dictfetchall()
                elif self.invoice_initial_date:
                    self.env.cr.execute(
                        query2 + " and account_move.company_id=%(company_id)s and account_move.date >= %(invoice_initial_date)s and account_move.date <= %(invoice_final_date)s and account_move.payment_date <= %(payment_final_date)s and account_move.payment_state in('paid','in_payment') order by account_move.id",
                        {"invoice_initial_date": self.invoice_initial_date,
                         "invoice_final_date": today,
                         "payment_final_date": self.payment_final_date,
                         'company_id': self.env.company.id})
                    excel_results = self.env.cr.dictfetchall()
                elif self.invoice_final_date:
                    self.env.cr.execute(
                        query2 + " and account_move.company_id=%(company_id)s and account_move.date <= %(invoice_final_date)s and account_move.payment_date <= %(payment_final_date)s and account_move.payment_state in('paid','in_payment') order by account_move.id",
                        {"invoice_final_date": self.invoice_final_date,
                         "payment_final_date": self.payment_final_date,
                         'company_id': self.env.company.id})
                    excel_results = self.env.cr.dictfetchall()
                else:
                    self.env.cr.execute(
                        query2 + " and account_move.company_id=%(company_id)s and account_move.payment_state in('paid','in_payment') and account_move.payment_date <= %(payment_final_date)s order by account_move.id",
                        {'company_id': self.env.company.id,
                         "payment_final_date": self.payment_final_date
                         })
                    excel_results = self.env.cr.dictfetchall()

            else:
                if self.invoice_initial_date and self.invoice_final_date:
                    self.env.cr.execute(
                        query2 + " and account_move.company_id=%(company_id)s and account_move.date >= %(invoice_initial_date)s and account_move.date <= %(invoice_final_date)s and account_move.payment_state in('paid','in_payment') order by account_move.id",
                        {"invoice_initial_date": self.invoice_initial_date,
                         "invoice_final_date": self.invoice_final_date,
                         'company_id': self.env.company.id})
                    excel_results = self.env.cr.dictfetchall()

                elif self.invoice_initial_date:
                    self.env.cr.execute(
                        query2 + " and account_move.company_id=%(company_id)s and account_move.date >= %(invoice_initial_date)s and account_move.date <= %(invoice_final_date)s and account_move.payment_state in('paid','in_payment') order by account_move.id",
                        {"invoice_initial_date": self.invoice_initial_date,
                         "invoice_final_date": today,
                         'company_id': self.env.company.id})
                    excel_results = self.env.cr.dictfetchall()

                elif self.invoice_final_date:
                    self.env.cr.execute(
                        query2 + " and account_move.company_id=%(company_id)s and account_move.date <= %(invoice_final_date)s and account_move.payment_state in('paid','in_payment') order by account_move.id",
                        {"invoice_final_date": self.invoice_final_date,
                         'company_id': self.env.company.id})
                    excel_results = self.env.cr.dictfetchall()

                else:
                    self.env.cr.execute(
                        query2 + " and account_move.company_id=%(company_id)s and account_move.payment_state in('paid','in_payment') order by account_move.id",
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
        sheet.set_row(0, 35)
        head = workbook.add_format(
            {'align': 'center', 'valign': 'left', 'bold': True,
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
        if self.report_detail != 'invoice_line_detail':
            sheet.write('J1', 'Date', date_format)
            sheet.write('K1', data['todate'], date_content)
        else:
            sheet.write('O1', 'Date', date_format)
            sheet.write('P1', data['todate'], date_content)

        # sub titles
        row_number = 2
        column_count = 0
        sheet.write(row_number, column_count, 'Invoice No', sub_head)
        column_count += 1
        sheet.write(row_number, column_count, 'Invoice Date', sub_head)
        column_count += 1
        sheet.write(row_number, column_count, 'Sales Team', sub_head)
        column_count += 1
        sheet.write(row_number, column_count, 'Seller', sub_head)
        column_count += 1
        sheet.write(row_number, column_count, 'Client Name', sub_head)
        column_count += 1
        sheet.write(row_number, column_count, 'Invoice Date Due', sub_head)
        column_count += 1
        sheet.write(row_number, column_count, 'Invoice Currency', sub_head)
        column_count += 1
        if self.env.ref('base.main_company').currency_id.name != 'MXN':
            sheet.write(row_number, column_count, 'Exchange Rate', sub_head)
            column_count += 1
        if data['line'] == 1:
            sheet.write(row_number, column_count, 'Product', sub_head)
            column_count += 1
            sheet.write(row_number, column_count, 'Quantity', sub_head)
            column_count += 1
            sheet.write(row_number, column_count, 'Sale Cost', sub_head)
            column_count += 1
            if self.env.ref('base.main_company').currency_id.name != 'MXN':
                sheet.write(row_number, column_count, 'Sale Cost MXN',
                            sub_head)
                column_count += 1
            sheet.write(row_number, column_count, 'Unit Price', sub_head)
            column_count += 1
            if self.env.ref('base.main_company').currency_id.name != 'MXN':
                sheet.write(row_number, column_count, 'Unit Price MXN', sub_head)
                column_count += 1
            sheet.write(row_number, column_count, 'Margin', sub_head)
            column_count += 1
            if self.env.ref('base.main_company').currency_id.name != 'MXN':
                sheet.write(row_number, column_count, 'Margin MXN', sub_head)
                column_count += 1
        sheet.write(row_number, column_count, 'Invoice Subtotal', sub_head)
        column_count += 1
        sheet.write(row_number, column_count, 'Total', sub_head)
        column_count += 1
        if self.env.ref('base.main_company').currency_id.name != 'MXN':
            sheet.write(row_number, column_count, 'Total Amount MXN', sub_head)
            column_count += 1
        sheet.write(row_number, column_count, 'Amount Paid', sub_head)
        column_count += 1
        if self.env.ref('base.main_company').currency_id.name != 'MXN':
            sheet.write(row_number, column_count, 'Paid Amount MXN', sub_head)
            column_count += 1
        sheet.write(row_number, column_count, 'Invoice Paid Date', sub_head)

        row_number = 3
        for i in data['excel_result']:
            column_count = 0
            sheet.write(row_number, column_count, i['invoice_number'],cell_content)
            column_count += 1
            sheet.write(row_number, column_count, i['invoice_created_date'], cell_content)
            column_count += 1
            sheet.write(row_number, column_count, i['sales_team'], cell_content)
            column_count += 1
            sheet.write(row_number, column_count, i['sales_person'], cell_content)
            column_count += 1
            sheet.write(row_number, column_count, i['client_name'],cell_content)
            column_count += 1
            sheet.write(row_number, column_count, i['invoice_date_due'],cell_content)
            column_count += 1
            sheet.write(row_number, column_count, i['currency'],cell_content)
            column_count += 1
            if self.env.ref('base.main_company').currency_id.name != 'MXN':
                sheet.write(row_number, column_count, data['exchange_rate'], cell_content)
                column_count += 1
            if data['line'] == 1:
                sheet.write(row_number, column_count, i['line_product'], cell_content)
                column_count += 1
                sheet.write(row_number, column_count, i['line_quantity'], cell_content)
                column_count += 1
                sheet.write(row_number, column_count, i['line_quantity']*i['standard_price'],cell_content)
                column_count += 1
                if self.env.ref('base.main_company').currency_id.name != 'MXN':
                    sheet.write(row_number, column_count, data['exchange_rate']*(i['line_quantity']*i['standard_price']),cell_content)
                    column_count += 1
                sheet.write(row_number, column_count, i['line_subtotal'], cell_content)
                column_count += 1
                if self.env.ref('base.main_company').currency_id.name != 'MXN':
                    sheet.write(row_number, column_count, data['exchange_rate'] * i['line_subtotal'], cell_content)
                    column_count += 1
                sheet.write(row_number, column_count,i['line_subtotal']-(i['line_quantity']*i['standard_price']),cell_content)
                column_count += 1
                if self.env.ref('base.main_company').currency_id.name != 'MXN':
                    sheet.write(row_number, column_count, data['exchange_rate']*(i['line_subtotal']-(i['line_quantity']*i['standard_price'])), cell_content)
                    column_count += 1
            sheet.write(row_number, column_count, i['subtotal_amount'],cell_content)
            column_count += 1
            sheet.write(row_number, column_count, i['total_amount'],cell_content)
            column_count += 1
            if self.env.ref('base.main_company').currency_id.name != 'MXN':
                sheet.write(row_number, column_count, (data['exchange_rate'] * i['total_amount']), cell_content)
                column_count += 1
            if i['invoice_paid_date']:
                sheet.write(row_number, column_count,i['invoice_paid_amount'],cell_content)
                column_count += 1
                if self.env.ref('base.main_company').currency_id.name != 'MXN':
                    sheet.write(row_number, column_count, (data['exchange_rate'] * i['invoice_paid_amount']), cell_content)
                    column_count += 1
                sheet.write(row_number, column_count, i['invoice_paid_date'], cell_content)
                column_count += 1
            else:
                sheet.write(row_number, column_count, 0, cell_content)
                column_count += 1
                if self.env.ref('base.main_company').currency_id.name != 'MXN':
                    sheet.write(row_number, column_count, (data['exchange_rate'] * i['invoice_paid_amount']), cell_content)
                    column_count += 1
                sheet.write(row_number, column_count, '', cell_content)
            row_number += 1
        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()
