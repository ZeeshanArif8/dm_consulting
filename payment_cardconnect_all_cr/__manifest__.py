# -*- coding: utf-8 -*-
# Part of Odoo Module Developed by Candidroot Solutions Pvt. Ltd.
# See LICENSE file for full copyright and licensing details.

{
    'name': "CardConnect Subscription Payment Acquirer",
    'version': '14.0.1.0',
    'summary': """
        Integrate Cardconnect Subscription Payment with Odoo. With this module, your customers can pay for their online orders with Cardconnect payment gateway on Odoo website.
    """,
    "license": "Other proprietary",
    'description': """
Description
-----------
    - CardConnect Payment Acquirer
    """,
    'author': "Candidroot Solutions Pvt. Ltd.",
    'website': "https://www.candidroot.com/",
    'category': 'Payment',
    'depends': ['website_sale','account_payment'],
    'data': [
        'security/ir.model.access.csv',
        'views/payment_acquirer.xml',
        'views/payment_views.xml',
        'data/payment_acquirer_data.xml',
        'views/sale_view.xml',
        'views/portal.xml',
        'wizard/payment_refund.xml',
        'wizard/payment_token.xml',
    ],
    'demo': [],
    'images': ['static/description/banner.jpg'],
    'qweb': [],
    'installable': True,
    'live_test_url': '',
    'auto_install': False,
    'application': False,
    'post_init_hook': 'create_missing_journal_for_acquirers',
    'uninstall_hook': 'uninstall_hook',
    'price': 49.99,
    'currency': 'USD',
}
