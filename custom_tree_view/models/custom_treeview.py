# -*- coding: utf-8 -*-
from odoo import models, fields, api


class AccountMoveInherit(models.Model):
    _inherit = 'account.move'
    cost = fields.Float(string='Cost', store="True")
    margin = fields.Float(string='Margin', store="True")

    @api.model
    def create(self, vals):
        res = super(AccountMoveInherit, self).create(vals)
        calculated_cost = 0.0
        calculated_margin = 0.0
        if res:
            for line in res.invoice_line_ids:
                calculated_cost += line.quantity * line.product_id.standard_price
                if line.price_unit:
                    calculated_margin += line.quantity * line.price_unit
                else:
                    calculated_margin += line.quantity * line.product_id.list_price
        res.cost = calculated_cost
        res.margin = calculated_margin - calculated_cost
        return res

    def action_post(self):
        res = super(AccountMoveInherit, self).action_post()
        calculated_cost = 0.0
        calculated_margin = 0.0
        if self:
            for line in self.invoice_line_ids:
                calculated_cost += line.quantity * line.product_id.standard_price
                calculated_margin += line.quantity * line.price_unit
        self.cost = calculated_cost
        self.margin = calculated_margin - calculated_cost
        return res

    def write(self, vals):
        calculated_cost = 0.0
        calculated_margin = 0.0
        if self.state == 'draft':
            for line in self.invoice_line_ids:
                calculated_cost += line.quantity * line.product_id.standard_price
                calculated_margin += line.quantity * line.price_unit
            vals['margin'] = calculated_margin - calculated_cost
            vals['cost'] = calculated_cost
            rec = super(AccountMoveInherit, self).write(vals)
            return rec
