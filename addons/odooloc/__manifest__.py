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
    'depends': ['purchase', 'product', 'stock', 'base'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        # 'views/templates.xml',
        'views/layout.xml',
        'views/views.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo.xml',
    ],
}