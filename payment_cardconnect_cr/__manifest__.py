# -*- coding: utf-8 -*-
# Part of Odoo Module Developed by Candidroot Solutions Pvt. Ltd.
# See LICENSE file for full copyright and licensing details.

{
    'name': "CardConnect Payment Acquirer",
    'version': '14.0.1.0',
    'summary': """
        Integrate Cardconnect Payment with Odoo. With this module, your customers can pay for their online orders with Cardconnect payment gateway on Odoo website.
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
    'depends': ['payment', 'website_sale'],
    'data': [
        'security/ir.model.access.csv',
        'static/src/xml/template.xml',
        'views/payment_acquirer.xml',
        'views/payment_views.xml',
        'views/payment_cardconnect.xml',
        'data/payment_acquirer_data.xml',
    ],
    'demo': [
    ],
    'images': ['static/description/banner.jpg'],
    'qweb': [],
    'installable': True,
    'live_test_url': '',
    'auto_install': False,
    'application': False,
    'post_init_hook': 'create_missing_journal_for_acquirers',
    'uninstall_hook': 'uninstall_hook',
}
