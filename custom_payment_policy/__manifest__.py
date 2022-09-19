# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2022-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Technologies Pvt. Ltd (<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
{
    'name': 'Custom Payment Policy',
    'category': 'Accounting/Accounting',
    'version': '15.0.0.0.1',
    'summary': 'Custom Payment Policy',
    'description': 'Custom Payment Policy',
    'depends': ['base', 'account_accountant','l10n_mx_edi'],
    'website': 'https://www.cybrosys.com',
    'data': ['views/custom_payment_policy.xml'],
    'post_init_hook': '_post_init_payment_policy',
    'license': 'LGPL-3',
    'author': 'Cybrosys',
}
