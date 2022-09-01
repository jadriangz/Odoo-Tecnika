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
    'name': 'Custom Invoice Tree View',
    'category': 'Accounting/Accounting',
    'version': '15.0.1.0.0',
    'author': 'Cybrosys',
    'summary': 'Custom Invoice Tree View',
    'description': 'Custom Invoice Tree View',
    'depends': ['base', 'account'],
    'website': 'https://www.cybrosys.com/',
    'data': ['views/custom_treeview.xml'],
    'post_init_hook': '_post_init_custom_tree_view',
    'installable': True,
    'license': 'LGPL-3',
}
