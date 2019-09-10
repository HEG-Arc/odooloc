# -*- coding: utf-8 -*-
{
    'name': "odooloc",

    'summary': """Module permettant la gestion de la location de matériel""",

    'description': """
        Permet d'ajouter les éléments nécessaires afin d'assurer la gestion de location de matériel dans Odoo.
    """,

    'author': "HEG-Arc",
    'website': "https://www.he-arc.ch/gestion",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Test',
    'version': '0.1',
    'application': True,

    # any module necessary for this one to work correctly
    'depends': ['base','sale_management','purchase','stock','sale_stock','mrp','mail','account_invoicing', 'purchase','maintenance','board',
                'account_chart_template_multicompany'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        # 'views/templates.xml',
        'data/ir.sequence.csv',
        'views/res_config_settings.xml',
        'views/odooloc_layout.xml',
        'views/odooloc.xml',
        'views/product_template.xml',
        'data/product.category.csv',
        'data/res.partner.csv',
        'data/product.template.csv',
        'data/stock.warehouse.csv',
        'data/stock.location.csv',
        'data/stock.production.lot.csv',
        'data/stock.picking.type.csv'
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo.xml',
    ],
}