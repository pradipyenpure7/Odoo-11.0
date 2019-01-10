{
    'name': 'Sunfire Sales Tweak',
    'version': '11.0.1.0.0',
    'summary': 'Sunfire Sales Tweak',
    'category': 'Sales',
    'author': 'Jeevan',
    'maintainer': 'Jeevan',
    'website': 'www.saiaipl.com',
    'license': 'AGPL-3',
    'depends': [
        'sale','product','sale_margin','account','purchase','crm','sale_order_dates','account','web'
    ],
    'data': [
        'security/security_group.xml',
	'views/sunfire_sale_views.xml',
        'views/sunfire_sales_actions.xml',
        'views/sunfire_sales_menus.xml',
        'views/sunfire_sales_buttons.xml',
        'views/sunfire_sales_trees.xml',
        'views/res_partner_views.xml',
        'views/sunfire_master_menu_views.xml',
        
        'views/ref_template.xml',
        # 'views/trees_view.xml',
        # 'views/opf_cancel_tree.xml',
        'wizard/sunfire_import_view.xml',
        # 'report/sales_quat_report.xml',
        # 'report/sales_order.xml',
        'report/quotation_report.xml',
        'report/opf_report.xml',
        'report/mis_report.xml',
        'report/pipeline_report.xml'
    ],
    
    'installable': True,
    'auto_install': False,
    'application': False,
}

