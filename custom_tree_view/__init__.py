# -*- coding: utf-8 -*-
from . import models
from odoo import api, SUPERUSER_ID


def _post_init_custom_tree_view(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    cr.execute(""" select account_move.id 
        from account_move where 
        account_move.move_type = 'out_invoice' """)
    ac_id = cr.dictfetchall()
    cr.execute(""" select account_account.id 
            from account_account where 
            account_account.internal_group = 'income' or  
            account_account.internal_group = 'asset' """)
    ac_name = cr.dictfetchall()
    if ac_id and ac_name:
        for i in ac_id:
            for k in ac_name:
                cr.execute(""" select account_move.id,product_template.name, 
                        product_template.list_price,account_move_line.quantity,account_move.amount_untaxed_signed,
                        ir_property.value_float as standard_price, 
                        account_move.name
                        from product_template inner join product_product
                        on product_product.product_tmpl_id = product_template.id
                        inner join ir_property
                        on ir_property.res_id = 'product.product,' || product_product.id
                        inner join account_move_line on
                        account_move_line.product_id = product_product.id
                        inner join account_move on
                        account_move.id = account_move_line.move_id
                        where account_move.move_type = 'out_invoice' and 
                        account_move_line.account_id =%(in_ac_id)s 
                        and account_move.id =%(ac_id)s """,
                           {"in_ac_id": k['id'],
                            "ac_id": i['id']})
                data = cr.dictfetchall()
                if data:
                    standard_price = 0
                    for j in data:
                        if not j['quantity']:
                            standard_price += j['standard_price'] * 0
                        else:
                            standard_price += j['standard_price'] * j[
                                'quantity']
                        env['account.move'].browse(int(i['id'])).write({
                            'margin': j['amount_untaxed_signed'] - standard_price,
                            'cost': standard_price,
                        })
