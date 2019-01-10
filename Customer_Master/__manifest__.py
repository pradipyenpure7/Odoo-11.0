# -*- coding: utf-8 -*-
{
    'name': "Customer_Master",
    'summary': """
        All Master Views and Models in this app
        """,
    'description': """
        Long description of module's purpose
    """,
    'author': "Hrishikesh S. Kulkarni",
    'website': "http://www.saiaipl.com",
    'category': 'Master',
    'version': '1.1',
    # any module necessary for this one to work correctly
    'depends': ['base'],
    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/res_partner_views.xml'
    ],
    # only loaded in demonstration mode
#     'demo': [
#         'demo/demo.xml',
#     ],
    'installable':True,
    'auto_install':False,
    'application':True,
}