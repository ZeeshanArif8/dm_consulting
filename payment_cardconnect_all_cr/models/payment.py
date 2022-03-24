# -*- coding: utf-8 -*-
# Part of Odoo Module Developed by Candidroot Solutions Pvt. Ltd.
# See LICENSE file for full copyright and licensing details.

import logging
import pprint
from odoo import api, fields, models, _
from odoo.addons.payment.models.payment_acquirer import ValidationError
from odoo.tools.float_utils import float_compare
from .. import cardconnect
_logger = logging.getLogger(__name__)

class AcquirerCardconnect(models.Model):
    _inherit = 'payment.acquirer'

    provider = fields.Selection(selection_add=[('cardconnect', 'Card Connect')], ondelete={'cardconnect': 'set default'})
    cconnect_merchant_account = fields.Char('Merchant Account', required_if_provider='cardconnect', groups='base.group_user')
    cconnect_url = fields.Char('CardConnect URL', required_if_provider='cardconnect', groups='base.group_user')
    cconnect_user = fields.Char("Card Connect User", required_if_provider='cardconnect', groups='base.group_user')
    cconnect_pwd = fields.Char("Card Connect Password", required_if_provider='cardconnect', groups='base.group_user')

    def _get_feature_support(self):
        res = super(AcquirerCardconnect, self)._get_feature_support()
        res['fees'].append('cardconnect')
        res['tokenize'].append('cardconnect')
        return res

    def cardconnect_compute_fees(self, amount, currency_id, country_id):
        if not self.fees_active:
            return 0.0
        if country_id:
            country_id = self.env['res.country'].browse(country_id)
        if country_id and self.company_id.sudo().country_id.id == country_id.id:
            percentage = self.fees_dom_var
            fixed = self.fees_dom_fixed
        else:
            percentage = self.fees_int_var
            fixed = self.fees_int_fixed
        # fees = (percentage / 100.0 * amount + fixed) / (1 - percentage / 100.0)
        fees = (amount + fixed) * percentage / 100.0
        return fees

    @api.model
    def _get_cardconnect_urls(self, environment):
        return {
            'cardconnect_main_url': '/payment/cardconnect',
        }

    def cardconnect_get_form_action_url(self):
        environment = 'prod' if self.state == 'enabled' else 'test'
        return self._get_cardconnect_urls(environment)['cardconnect_main_url']

    def cardconnect_s2s_form_validate(self, data):
        error = dict()
        mandatory_fields = ["cc_number", "cc_cvc", "cc_holder_name", "cc_expiry", "cc_brand"]
        for field_name in mandatory_fields:
            if not data.get(field_name):
                error[field_name] = 'missing'
        return False if error else True

    def cardconnect_s2s_form_process(self, data):
        acquirer_id = self.env['payment.acquirer'].sudo().browse(int(data.get('acquirer_id')))
        partner = self.env.user.partner_id
        cardconnect.username = acquirer_id.cconnect_user
        cardconnect.password = acquirer_id.cconnect_pwd
        cardconnect.base_url = acquirer_id.cconnect_url
        cardconnect.debug = True
        result = cardconnect.Profile.create(
            merchid=acquirer_id.cconnect_merchant_account,
            account=data.get('cc_number'),
            name=data.get('cc_holder_name'),
            expiry=data.get('cc_expiry'),
        )
        if result and result.get('respcode') == '09':
            token = self.env['payment.token'].sudo().create({
                'name': data.get('cc_number'),
                'acquirer_ref': result.get('profileid'),
                'acctid': result.get('acctid'),
                'acquirer_id': acquirer_id.id,
                'partner_id': partner.id,
            })
            a = token.name
            name = a[-4:].rjust(len(a), "X")
            token.name = name
            token.short_name = name
            token.verified = True
            return token
        else:
            ValidationError('api response not found')

class TransactionCardconnect(models.Model):
    _inherit = 'payment.transaction'

    cct_txnid = fields.Char('Transaction ID')
    cct_txcurrency = fields.Char('Transaction Currency')
    state = fields.Selection(selection_add=[('refund', 'Refund'),
                                            ('partial_refund', 'Partial Refund'),
                                            ('void', 'Void'),
                                            ('partial_void', 'Partial Void')],ondelete={'refund': 'set default', 'partial_refund': 'set default', 'void': 'set default', 'partial_void': 'set default'})
    refund_amount = fields.Float('Refund/Void Amount')
    cc_response = fields.Text("Card Connect Response")

    # def _check_amount_and_confirm_order(self):
    #     self.ensure_one()
    #     if self.acquirer_id and self.acquirer_id.provider == 'cardconnect':
    #         for order in self.sale_order_ids.filtered(lambda so: so.state in ('draft', 'sent')):
    #             if order.currency_id.compare_amounts(self.amount + self.fees, order.amount_total) == 0:
    #                 order.with_context(send_email=True).action_confirm()
    #             else:
    #                 _logger.warning(
    #                     '<%s> transaction AMOUNT MISMATCH for order %s (ID %s): expected %r, got %r',
    #                     self.acquirer_id.provider, order.name, order.id,
    #                     order.amount_total, self.amount,
    #                 )
    #                 order.message_post(
    #                     subject=_("Amount Mismatch (%s)", self.acquirer_id.provider),
    #                     body=_("The order was not confirmed despite response from the acquirer (%s): order total is %r but acquirer replied with %r.") % (
    #                              self.acquirer_id.provider,
    #                              order.amount_total,
    #                              self.amount,
    #                          )
    #                 )
    #     else:
    #         return super(TransactionCardconnect)._check_amount_and_confirm_order()

    def cardconnect_s2s_do_transaction(self, **data):
        cardconnect.username = self.acquirer_id.cconnect_user
        cardconnect.password = self.acquirer_id.cconnect_pwd
        cardconnect.base_url = self.acquirer_id.cconnect_url
        cardconnect.debug = True
        auth_result = cardconnect.Auth.create(
            merchid=self.acquirer_id.cconnect_merchant_account,
            profile=self.payment_token_id.acquirer_ref + '/' + self.payment_token_id.acctid,
            amount=self.amount,
            currency=self.currency_id.name,
        )
        if auth_result and auth_result.get('respcode') == '00' and auth_result.get("retref"):
            auth_result = cardconnect.Capture.create(
                merchid=self.acquirer_id.cconnect_merchant_account,
                retref=auth_result['retref'],
            )
        return self._cardconnect_s2s_validate_tree(auth_result)

    def _cardconnect_s2s_validate_tree(self, result):
        return self._cardconnect_s2s_validate(result)

    def _cardconnect_s2s_validate(self, result):
        if result.get('respstat') == "A":
            self.write({
                'cct_txnid': result.get('retref'),
                'cct_txcurrency': self.currency_id.name,
                'acquirer_reference': result.get('retref'),
                'date': fields.Datetime.now(),
                'cc_response': result
            })
            self._set_transaction_done()
            return True
        elif result.get('respstat') == "C":
            error = result.get('resptext')
            _logger.info(error)
            self.write({
                'acquirer_reference': result.get('retref'),
            })
            self._set_transaction_error(msg=error)
            return False
        else:
            error = result.get('resptext')
            _logger.info(error)
            self.write({
                'acquirer_reference': result.get('retref'),
            })
            self._set_transaction_error(msg=error)
            return False

class PaymentToken(models.Model):
    _inherit = 'payment.token'

    acctid = fields.Char('CardConnect Account ID')