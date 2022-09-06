# -*- coding: utf-8 -*-
from odoo import fields, models, api


class CustomInvoiceWizard(models.TransientModel):
    _name = 'custom.invoice.wizard'
    line_ids = fields.One2many('custom.invoice.line.wizard', 'wizard_id')

    def update_content(self):
        active_id = self.env['account.move'].browse(
            self._context.get('active_id'))

        for line in self.line_ids:
            for inline in active_id.invoice_line_ids:
                if line.wizard_line_id.id == inline.id:
                    if inline.analytic_account_id:
                        inline.update(
                            {'analytic_account_id': line.analytical_account_id})
                        self.env.cr.execute(""" select account_analytic_line.id 
                        as account_id from account_move_line join account_analytic_line  
                        on account_analytic_line.move_id = account_move_line.id
                        where account_move_line.move_id =%(move_id)s""",
                        {"move_id": line.wizard_line_id.move_id.id})
                        analytical_change_ids = self.env.cr.dictfetchall()
                        for analytical_change_id in analytical_change_ids:
                            change_id = self.env[
                                'account.analytic.line'].browse(
                                analytical_change_id['account_id'])
                            change_id.update(
                                {'account_id': line.analytical_account_id})

    @api.model
    def default_get(self, fields_list):
        res = super(CustomInvoiceWizard, self).default_get(fields_list)
        active_id = self.env['account.move'].browse(
            self._context.get('active_id'))
        if active_id:
            lst = []
            lst.clear()
            for inline in active_id.invoice_line_ids:
                lst.append(
                    (0, 0, {'wizard_line_id': inline.id,
                            'product_id': inline.product_id,
                            'label': inline.name,
                            'analytical_account_id': inline.analytic_account_id}))
            res['line_ids'] = lst
        return res


class CustomInvoiceLIneWizard(models.TransientModel):
    _name = 'custom.invoice.line.wizard'
    wizard_id = fields.Many2one('custom.invoice.wizard')
    label = fields.Char()
    wizard_line_id = fields.Many2one('account.move.line')
    product_id = fields.Many2one('product.product')
    analytical_account_id = fields.Many2one('account.analytic.account')
