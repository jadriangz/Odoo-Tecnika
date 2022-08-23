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
    'name': 'Custom Payment',
    'category': 'Accounting/Accounting',
    'version': '15.0.0.0.1',
    'summary': 'Custom Payment',
    'description': 'Custom Payment',
    'depends': ['base', 'account_accountant'],
    'website': 'https://www.cybrosys.com',
    'sequence': 10,
    'assets': {
        'web.assets_backend': [
            'custom_payment/static/src/js/custom_payment.js',
        ],
        'web.assets_qweb': [
            'custom_payment/static/src/xml/custom_payment.xml',
        ],
    },
    'license': 'LGPL-3',
    'author': 'Cybrosys',
}
