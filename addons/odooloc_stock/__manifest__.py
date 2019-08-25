# -*- coding: utf-8 -*-
{
    'name': "odooloc_stock",

    'summary': """
        Module complémentaire à odooloc permettant la gestion des déplacements de stock
    """,

    'description': """
        Permet d'ajouter les éléments nécessaires afin d'assurer le suivi de produits lors de locations de matériel
    """,

    'author': "HEG-Arc",
    'website': "https://www.he-arc.ch/gestion",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Test',
    'version': '0.1',
    'application': False,

    # any module necessary for this one to work correctly
    'depends': ['odooloc'],

    # always loaded
    'data': [],

    # only loaded in demonstration mode
    'demo': [],

    'installable': True,
    'auto_install': True
}