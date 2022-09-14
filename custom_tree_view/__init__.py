# -*- coding: utf-8 -*-
from . import models
from odoo import api, SUPERUSER_ID


def _post_init_custom_tree_view(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    account_move_data = env['account.move'].search(
        [('move_type', '=', 'out_invoice')])
    account_account_data = env['account.account'].search(
        ['|', ('internal_group', '=', 'income'),
         ('internal_group', '=', 'asset')])
    for account_move_line in account_move_data:
        cost = 0
        price = 0
        margin_percentage = 0
        for account_account_line in account_account_data:
            account_move_line_data = env['account.move.line'].search(
                ['&', ('move_id', '=', account_move_line.id),
                 ('account_id', '=', account_account_line.id)])
            if account_move_line_data:
                for account_move_line_data_line in account_move_line_data:
                    cost += account_move_line_data_line.product_id.standard_price * account_move_line_data_line.quantity
        price = account_move_line.amount_untaxed_signed
        margin = price - cost
        if margin > 0 and price > 0:
            margin_percentage = (margin * 100) / price
        env['account.move'].browse(int(account_move_line['id'])).write({
            'margin': margin,
            'cost': cost,
            'margin_percentage': margin_percentage})
