# -*- coding: utf-8 -*-

from odoo import api, models, fields, _
from odoo.exceptions import UserError
from .. import cardconnect

class SalePaymentToken(models.TransientModel):
    _name = "sale.payment.token"
    _description = "Sale Payment Token"

    partner_id = fields.Many2one('res.partner',string='Partner')
    name = fields.Char(string='Name')
    account = fields.Char(string="Account")
    expiry = fields.Char(string="Expiry")

    def create_new_payment_token(self):
        acquirer_id = self.env['payment.acquirer'].sudo().search([('provider', '=', 'cardconnect')], limit=1)
        partner = self.partner_id
        if acquirer_id and partner:
            try:
                cardconnect.username = acquirer_id.cconnect_user
                cardconnect.password = acquirer_id.cconnect_pwd
                cardconnect.base_url = acquirer_id.cconnect_url
                cardconnect.debug = True
                result = cardconnect.Profile.create(
                    merchid=acquirer_id.cconnect_merchant_account,
                    account=self.account,
                    name=self.name,
                    expiry=self.expiry,
                )
                if result and result.get('respcode') == '09':
                    token = self.env['payment.token'].sudo().create({
                        'name': self.account,
                        'acquirer_ref': result.get('profileid'),
                        'acctid': result.get('acctid'),
                        'acquirer_id': acquirer_id.id,
                        'partner_id': partner.id,
                    })
                    a = token.name
                    if len(a) >= 16:
                        # name = a[0:2] + 'XXXXXXXXXX' + a[12:16]
                        name = a[-4:].rjust(len(a), "X")
                        token.name = name
                        token.short_name = name
                    token.verified = True
            except Exception as e:
                print(e)
                raise UserError(_(e))
        else:
            raise UserError(_("Acquirer/Partner not set"))