# -*- coding: utf-8 -*-
{
    'name': "opensim",

    'summary': """
        Plate-forme de simulation destinée aux jeux sérieux""",

    'description': """
        Permet aux utilisateurs d’expérimenter la gestion d’entreprise avec Odoo de manière dynamique et ludique.
        Les utilisateurs sont placés dans une situation de gestion d’entreprise proche de la réalité et doivent,
        à l’aide d'Odoo, piloter leur entreprise de manière à optimiser la création de valeur.
    """,

    'author': "HEG-Arc",
    'website': "https://odoosim.ch/",
    'application': True,

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'module_category_hr_gamification',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['opensim_time','sale_management','purchase','stock','sale_stock','mrp','mail','account_invoicing', 'purchase','maintenance','board',
                'account_chart_template_multicompany', 'l10n_ch', 'account_accountant_cbc','account_report_cbc'],
    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/layout.xml',
        'views/views.xml',
        #'views/templates.xml',
        'data/product.category.csv',
        'data/product.pricelist.csv',
        'data/res.partner.csv',
        'data/product.template.csv',
        'data/product_image.xml',
        'data/res.company.csv',
        'data/product.supplierinfo.csv',
        'data/res.users.csv',
        'data/stock.inventory.xml',
        'data/mrp.bom.xml'
        # 'data/functions.xml'
    ],
    'post_load': 'resume_simulation_thread',
    'post_init_hook':'post_init_hook',
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    # web client (js) qweb templates
    'qweb': [
        'static/src/xml/templates.xml'
    ]
}
