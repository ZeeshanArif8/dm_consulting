# -*- coding: utf-8 -*-
# Part of Odoo Module Developed by Candidroot Solutions Pvt. Ltd.
# See LICENSE file for full copyright and licensing details.
import logging
import pprint
from datetime import datetime

import werkzeug
from odoo import http
from odoo.http import request
from odoo.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.translate import _

from .. import cardconnect

_logger = logging.getLogger(__name__)

Error1 = _(
    "Cardconnect Errors 1: cardconnect Payment Gateway Currently not Configure for this Currency pls Connect Your Shop Provider !!!")
Error2 = _("Cardconnect Errors 2: Authentication Error: API keys are incorrect.")
Error3 = _("Cardconnect Errors 3: Authorization Error: not authorized to perform the attempted action.")
Error4 = _("Cardconnect Errors 4: Issue occure while generating clinet token, pls contact your shop provider.")
Error5 = _("Cardconnect Errors 5: Default 'Merchant Account ID' not found.")
Error6 = _("Cardconnect Errors 6: Transaction not Found.")
Error7 = _("Cardconnect Errors 7: Error occured while payment processing or Some required data missing.")
Error8 = _("Cardconnect Errors 8: Validation error occured. Please contact your administrator.")
Error9 = _(
    "Cardconnect Errors 9: Payment has been recevied on cardconnect end but some error occured during processing the order.")
Error10 = _("Cardconnect Errors 10: Unknow Error occured. Unable to validate the cardconnect payment.")
SuccessMsg = _("Payment Successfully recieved and submitted for settlement.")


class CarcconnectController(http.Controller):

    @http.route(["/cardconnect/client_token"], type='json', auth="public", website=True)
    def client_token(self):
        try:
            return {'status': True, 'token': "74892365423647392"}
        except Exception as e:
            _logger.error("************Cardconnect exception occured 'client_token' ------- exception=%r", e)  # debug
            return {'status': False, 'message': Error4}

    def get_transaction_vals(self, form_vals, order=None):
        transaction_vals_dict = {}
        nonce_from_the_client = form_vals.get('payment_method_nonce')
        merchant_account_id = self.get_merchant_account_id()
        if nonce_from_the_client and merchant_account_id['status']:
            customer_obj = order.partner_id
            partner_billing_obj = order.partner_invoice_id
            partner_shipping_obj = order.partner_shipping_id
            transaction_vals_dict = {
                "amount": form_vals.get('amount'),
                "order_id": order.name,
                "payment_method_nonce": nonce_from_the_client,
                "merchant_account_id": merchant_account_id['merchant_account_id'],
                "options": {
                    "submit_for_settlement": True
                },
                "customer": {
                    "first_name": str(customer_obj.name),
                    "company": str(customer_obj.street),
                    "email": str(customer_obj.email),
                    "phone": str(customer_obj.phone),
                },
                "billing": {
                    "first_name": str(partner_billing_obj.name),
                    "company": str(partner_billing_obj.street),
                    "street_address": str(partner_billing_obj.street2),
                    "locality": str(partner_billing_obj.city),
                    "region": str(partner_billing_obj.state_id.name),
                    "postal_code": str(partner_billing_obj.zip),
                    "country_name": str(partner_billing_obj.country_id.name),
                    "country_code_alpha2": str(partner_billing_obj.country_id.code)
                },
                "shipping": {
                    "first_name": str(partner_shipping_obj.name),
                    "street_address": str(partner_shipping_obj.street),
                    "locality": str(partner_shipping_obj.city),
                    "region": str(partner_shipping_obj.state_id.name),
                    "postal_code": str(partner_shipping_obj.zip),
                    "country_name": str(partner_shipping_obj.country_id.name),
                    "country_code_alpha2": str(partner_shipping_obj.country_id.code)
                }
            }
        return transaction_vals_dict

    def cardconnect_do_payment(self, **post):
        order, reference, tx = request.website.sale_get_order(), post.get('reference'), None
        values = {
            'status': False,
            'message': '',
            'redirect_brt': False,  # True value redirect on Cardconnnect error custom page
        }
        try:
            PaymentAcquirer = request.env['payment.acquirer']
            acquirere_id = \
                request.env['ir.model.data'].get_object_reference('payment_cardconnect_cr',
                                                                  'payment_acquirer_cconnect')[1]

            acquirer_credential = PaymentAcquirer.sudo().browse(acquirere_id)

            # environment = acquirer_credential.environment
            merchant_id = acquirer_credential.cconnect_merchant_account
            cconnect_url = acquirer_credential.cconnect_url
            cconnect_user = acquirer_credential.cconnect_user
            cconnect_pwd = acquirer_credential.cconnect_pwd
            customer_obj = order.partner_id
            cardconnect.username = cconnect_user
            cardconnect.password = cconnect_pwd
            cardconnect.base_url = cconnect_url
            cardconnect.debug = True
            if reference:
                tx = request.env['payment.transaction'].sudo().search([('reference', '=', reference)])
            if tx:
                result = cardconnect.Auth.create(
                    merchid=merchant_id,
                    account=post.get('cardnumber'),
                    expiry=post.get('cardExpiry'),
                    amount=post.get('amount'),
                    cvv2=post.get('cardCVC'),
                    orderid=reference,
                    currency=post.get('currency'),
                    name=str(customer_obj.name),
                    address=str(customer_obj.street),
                    city=str(customer_obj.city),
                    country=str(customer_obj.country_id.code),
                    postal=str(customer_obj.zip),
                    email=str(customer_obj.email),
                    phone=str(customer_obj.phone),
                    profile="Y",
                    ecomind="E",
                    capture="Y"
                )
                if result.get('respstat') == "A":
                    values.update({
                        'status': True if result.get('respstat') == "A" else False,
                        'reference': reference,
                        'currency': post.get('currency'),
                        'amount': result.get('amount'),
                        'acquirer_reference': result.get('token'),
                        'partner_reference': post,
                        'tx_msg': SuccessMsg
                    })
                    _logger.info('Cardconnect form_feedback with values %s', pprint.pformat(values))  # debug
                    res = request.env['payment.transaction'].sudo().form_feedback(values, 'cardconnect')
                    if not res:
                        tx.sudo()._set_transaction_error(Error8)
                        values.update({
                            'status': False,
                            'redirect_brt': False,
                            'message': Error8,
                        })
                else:
                    values.update({
                        'status': False,
                        'reference': reference,
                        'currency': post.get('currency'),
                        'amount': result.get('amount'),
                        'acquirer_reference': result.get('token'),
                        'partner_reference': post,
                        'tx_msg': "Payment Failed"
                    })
                    _logger.info('Cardconnect form_feedback with values %s', pprint.pformat(values))  # debug
                    res = request.env['payment.transaction'].sudo().form_feedback(values, 'cardconnect')
                    if not res:
                        tx.sudo()._set_transaction_error(Error8)
                        values.update({
                            'status': False,
                            'redirect_brt': False,
                            'message': Error8,
                        })
            elif not tx:
                values.update({'status': False, 'redirect_brt': True, 'message': Error6})
            else:
                # more condition can we added
                values.update({'status': False, 'redirect_brt': True, 'message': Error7})
        except Exception as e:
            _logger.error(
                "************Cardconnect exception occured ******************** \n 'cardconnect_payment' ------- exception=%r",
                e)  # debug
            if reference:
                tx = request.env['payment.transaction'].search([('reference', '=', reference)])

            if tx and values['status']:
                tx.sudo().write({
                    'cct_txnid': values['acquirer_reference'],
                    'acquirer_reference': values['acquirer_reference'],
                    'state': 'error',
                    'date': datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                    'state_message': Error9,
                })
                values.update({'status': False, 'redirect_brt': True, 'message': Error9})
            elif tx and not values['status']:
                tx.sudo()._set_transaction_error(Error1)
                values.update({'status': False, 'redirect_brt': True, 'message': e or Error1})
            elif not tx:
                values.update({'status': False, 'redirect_brt': True, 'message': Error6})
            else:
                values.update({'status': False, 'redirect_brt': True, 'message': Error10})
        return values

    @http.route('/payment/cardconnect', type='http', auth="public", website=True)
    def cardconnect_payment(self, **post):
        """ cardconnect Payment Controller """
        _logger.info('Beginning cardconnect with post data %s', pprint.pformat(post))  # debug
        result = self.cardconnect_do_payment(**post)

        if not result['status']:
            _logger.error(result['message'])
        return werkzeug.utils.redirect('/payment/process')

    @http.route(['/cardconnect/modal'], type='json', auth="public", methods=['POST'], website=True)
    def cardconnect_modal(self,**kw):
        order = request.website.sale_get_order()
        acquirere_id = request.website.get_cardconnect_payment_acquirere_id()
        acquirere = request.env['payment.acquirer'].sudo().browse(int(acquirere_id))
        vals = {
            'return_url': '/shop/payment/validate',
            'reference': '/',
            'amount': kw.get('order_amount') if kw.get('order_amount') and kw.get('after_payment') else order.amount_total,
            'currency': order.currency_id,
            'cardconnect-acquirer-id': acquirere_id,
        }
        return request.env['ir.ui.view']._render_template("payment_cardconnect_cr.cardconnect_template_modal", vals)
