# -*- coding: utf-8 -*-
from odoo import models, fields, api


class AccountMoveInherit(models.Model):
    _inherit = 'account.move'
    cost = fields.Float(string='Cost', store="True")
    margin = fields.Float(string='Margin', store="True")
    margin_percentage = fields.Float(string='Margin Percentage', store="True")

    @api.model
    def create(self, vals):
        res = super(AccountMoveInherit, self).create(vals)
        calculated_cost = 0.0
        calculated_margin = 0.0
        calculated_subtotal = 0.0
        if res:
            for line in res.invoice_line_ids:
                calculated_cost += line.quantity * line.product_id.standard_price
                calculated_subtotal += line.price_subtotal
                if line.price_unit:
                    calculated_margin += line.quantity * line.price_unit
                else:
                    calculated_margin += line.quantity * line.product_id.list_price
        margin = calculated_margin - calculated_cost
        res.cost = calculated_cost
        res.margin = margin
        if margin > 0 and calculated_subtotal > 0:
            res.margin_percentage = (margin * 100) / calculated_subtotal
        return res

    def action_post(self):
        res = super(AccountMoveInherit, self).action_post()
        calculated_cost = 0.0
        calculated_margin = 0.0
        calculated_subtotal = 0.0
        if self:
            for line in self.invoice_line_ids:
                calculated_cost += line.quantity * line.product_id.standard_price
                calculated_subtotal += line.price_subtotal
                calculated_margin += line.quantity * line.price_unit
        margin = calculated_margin - calculated_cost
        self.cost = calculated_cost
        self.margin = margin
        if margin > 0 and calculated_subtotal > 0:
            self.margin_percentage = (margin * 100) / calculated_subtotal
        return res
