# -*- coding: utf-8 -*-

{
    'name': "Shopify Connect",

    'summary': "Connecting Odoo with Shopify",

    'description': "Easy to connect your multiple Shopify stores with Odoo.",

    'author': "Softpulse Infotech",
    'website': "https://softpulseinfotech.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Sales',
    'version': '15.0.1.0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'board', 'web', 'sale'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'wizards/operation_wizard.xml',
        'wizards/message_popup.xml',
        'wizards/export_products_to_shopify.xml',
        'wizards/create_location.xml',
        'wizards/add_product_images_popup.xml',
        'wizards/preview_order_invoice_wizard.xml',
        'data/export_product_wizard_from_action.xml',
        'data/cron_file.xml',
        'data/data.xml',
        'reports/print_invoice_preview.xml',
        'reports/print_invoice.xml',
        'views/shopify_product.xml',
        'views/instance.xml',
        'views/customers.xml',
        'views/orders.xml',
        'views/test.xml',
        'views/cron.xml',
        'views/odoo_product.xml',
        'views/locations.xml',
        'views/dashboard.xml',
        'views/settings.xml',
        'views/views.xml'
    ],
    'assets': {
        'web.assets_backend': [
            'demo_shopify/static/css/style.css',
            'demo_shopify/static/css/document_css.css'
        ],
    },
    'qweb': [
        "static/src/xml/*.xml"
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
'images': ['static/description/banner.png'],
'license': "LGPL-3",
'installable': True,
'application': True,
'auto_install': False,
}

