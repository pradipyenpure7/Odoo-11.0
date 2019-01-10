# -*- coding: utf-8 -*-
{
    'name': "sunfire_support",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "My Company",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','sunfire_sales','mail'],

    # always loaded
    'data': [
        'security/support_groups.xml',
        'views/support_category_views.xml',
        'views/support_channel_views.xml',
        'views/support_severity_views.xml',
        'views/support_tag_views.xml',
        'views/sunfire_support_views.xml',
        'views/menus.xml',
        'views/email_template.xml'
    ],
    # only loaded in demonstration mode
    
}