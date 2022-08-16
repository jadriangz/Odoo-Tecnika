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
    'name': 'Custom Sales Report',
    'category': 'Sales/Sales',
    'version': '15.0.1.0.0',
    'summary': 'Custom Sales Report',
    'description': 'Custom Sales Report',
    'depends': ['base', 'sale_management', 'account'],
    'website': 'https://www.cybrosys.com/',
    'data': [
        'security/ir.model.access.csv',
        'wizard/custom_report_wizard.xml',
        'views/custom_report_menu.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'custom_report/static/src/js/action_manager.js',
        ],
    },
    'license': 'LGPL-3',
    'author': 'Cybrosys',
}
