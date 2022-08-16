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
    'name': 'Custom Editable Invoice',
    'category': 'Accounting/Accounting',
    'version': '15.0.1.0.0',
    'author': 'Cybrosys',
    'summary': 'Custom Editable Invoice',
    'description': 'Custom Editable Invoice',
    'depends': ['base', 'account_accountant'],
    'website': 'https://www.cybrosys.com/',
    'data': ['security/ir.model.access.csv',
             'wizard/custom_invoice_wizard.xml',
             'views/custom_invoice.xml'
             ],
    'installable': True,
    'license': 'LGPL-3',
}
