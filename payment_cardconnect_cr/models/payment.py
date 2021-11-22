# -*- coding: utf-8 -*-
# Part of Odoo Module Developed by Candidroot Solutions Pvt. Ltd.
# See LICENSE file for full copyright and licensing details.

import logging

from odoo import api, fields, models, _
from odoo.addons.payment.models.payment_acquirer import ValidationError
from odoo.tools.float_utils import float_compare

_logger = logging.getLogger(__name__)


class AcquirerCardconnect(models.Model):
    _inherit = 'payment.acquirer'

    provider = fields.Selection(selection_add=[('cardconnect', 'Card Connect')],
                                ondelete={'cardconnect': 'set default'})
    cconnect_merchant_account = fields.Char('Merchant Account', required_if_provider='cardconnect',
                                            groups='base.group_user')
    cconnect_url = fields.Char('CardConnect URL', required_if_provider='cardconnect', groups='base.group_user')
    cconnect_user = fields.Char("Card Connect User", required_if_provider='cardconnect', groups='base.group_user')
    cconnect_pwd = fields.Char("Card Connect Password", required_if_provider='cardconnect', groups='base.group_user')

    def cardconnect_form_generate_values(self, tx_values):
        self.ensure_one()
        cardconnect_tx_values = dict(tx_values)
        temp_cardconnect_tx_values = {
            'company': self.company_id.name,
            'amount': tx_values.get('amount'),
            'currency': tx_values.get('currency') and tx_values.get('currency') or '',
            'currency_id': tx_values.get('currency') and tx_values.get('currency').id or '',
            'address_line1': tx_values['partner_address'],
            'address_city': tx_values['partner_city'],
            'address_country': tx_values['partner_country'] and tx_values['partner_country'].name or '',
            'email': tx_values['partner_email'],
            'address_zip': tx_values['partner_zip'],
            'name': tx_values['partner_name'],
            'phone': tx_values['partner_phone'],
        }

        temp_cardconnect_tx_values['returndata'] = cardconnect_tx_values.pop('return_url', '')
        cardconnect_tx_values.update(temp_cardconnect_tx_values)
        return cardconnect_tx_values

    @api.model
    def _get_cardconnect_urls(self, environment):
        """ Cardconnect URLS """
        return {
            'cardconnect_main_url': '/payment/cardconnect',
        }

    def cardconnect_get_form_action_url(self):
        environment = 'prod' if self.state == 'enabled' else 'test'
        return self._get_cardconnect_urls(environment)['cardconnect_main_url']


class TransactionCardconnect(models.Model):
    _inherit = 'payment.transaction'

    cct_txnid = fields.Char('Transaction ID')
    cct_txcurrency = fields.Char('Transaction Currency')

    @api.model
    def _cardconnect_form_get_tx_from_data(self, data):
        _logger.info("********************form data=%r", data)
        reference, amount, currency, acquirer_reference = data.get('reference'), data.get('amount'), data.get(
            'currency'), data.get('acquirer_reference')

        if not reference or not amount or not currency or not acquirer_reference:
            error_msg = 'CardConnect: received data with missing reference (%s) or acquirer_reference (%s) or Amount (%s)' % (
                reference, acquirer_reference, amount)
            _logger.error(error_msg)
            raise ValidationError(error_msg)

        tx = self.search([('reference', '=', reference)])
        if not tx or len(tx) > 1:
            error_msg = _('received data for reference %s') % (pprint.pformat(reference))
            if not tx:
                error_msg += _('; no order found')
            else:
                error_msg += _('; multiple order found')
            _logger.info(error_msg)
            raise ValidationError(error_msg)

        return tx

    def _cardconnect_form_get_invalid_parameters(self, data):
        invalid_parameters = []
        if float_compare(float(data.get('amount', '0.0')), self.amount, 2) != 0:
            invalid_parameters.append(('amount', data.get('amount'), '%.2f' % self.amount))
        if data.get('currency') != self.currency_id.name:
            invalid_parameters.append(('currency', data.get('currency'), self.currency_id.name))
        return invalid_parameters

    def _cardconnect_form_validate(self, data):
        status = data.get('status')
        res = {
            'cct_txnid': data.get('acquirer_reference'),
            'acquirer_reference': data.get('acquirer_reference'),
            'state_message': data.get('tx_msg'),
            'cct_txcurrency': data.get('currency'),
        }
        if status:
            _logger.info('Validated Cardconnect payment for tx %s: set as done' % (self.reference))
            self._set_transaction_done()
            return self.write(res)


class Website(models.Model):
    _inherit = 'website'

    @api.model
    def get_cardconnect_payment_acquirere_id(self):
        IrModelData = self.env['ir.model.data']
        print(IrModelData.sudo().get_object_reference('payment_cardconnect_cr', 'payment_acquirer_cconnect'))
        acquirere_id = IrModelData.sudo().get_object_reference('payment_cardconnect_cr', 'payment_acquirer_cconnect')[1]
        return acquirere_id if acquirere_id else 0
