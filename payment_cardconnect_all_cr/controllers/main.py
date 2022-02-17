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
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager, get_records_pager
from odoo.exceptions import UserError
from odoo.addons.payment.models.payment_acquirer import ValidationError
from odoo.addons.payment.controllers.portal import PaymentProcessing
_logger = logging.getLogger(__name__)

class CarcconnectController(http.Controller):

    @http.route(['/payment/cardconnect/s2s/create_json_3ds'], type='json', auth='public', csrf=False)
    def cardconnect_s2s_create_json_3ds(self, verify_validity=False, **kwargs):
        if not kwargs.get('partner_id'):
            kwargs = dict(kwargs, partner_id=request.env.user.partner_id.id)
        token = False
        error = None
        try:
            token = request.env['payment.acquirer'].browse(int(kwargs.get('acquirer_id'))).s2s_process(kwargs)
        except Exception as e:
            error = str(e)
        if not token:
            res = {
                'result': False,
                'error': error,
            }
            return res
        res = {
            'result': True,
            'id': token.id,
            'short_name': token.short_name,
            '3d_secure': False,
            'verified': True,
        }
        return res

    # Portal
class CustomerPortal(CustomerPortal):

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        partner = request.env.user.partner_id
        payment_token_obj = request.env['payment.token'].sudo()
        if 'mypaymentcard_count' in counters:
            values['mypaymentcard_count'] = payment_token_obj.search_count([('partner_id', '=', partner.id)]) if payment_token_obj.check_access_rights('read',raise_exception=False) else 0
        return values

    @http.route(['/my/payment/tokens/add'], type='json', auth="public", website=True)
    def portal_my_payment_tokens_add(self, **post):
        acquirer = request.env['payment.acquirer'].sudo().search([('provider', '=', 'cardconnect')], limit=1)
        if not acquirer:
            raise UserError(_("set payment acquirer (provide = cardconnect)"))
        if acquirer and not acquirer.cconnect_merchant_account:
            raise UserError(_("set merchant account in payment acquirer)"))
        values = {
            'acquirer': acquirer
        }
        return request.env['ir.ui.view']._render_template('payment_cardconnect_all_cr.portal_my_payment_tokens_add', values)

    @http.route(['/form/payment/tokens/add'], type='http', auth="public", website=True)
    def portal_form_payment_tokens_add(self, **post):
        acquirer_id = request.env['payment.acquirer'].sudo().search([('provider', '=', 'cardconnect')], limit=1)
        partner = request.env.user.partner_id
        try:
            cardconnect.username = acquirer_id.cconnect_user
            cardconnect.password = acquirer_id.cconnect_pwd
            cardconnect.base_url = acquirer_id.cconnect_url
            cardconnect.debug = True
            result = cardconnect.Profile.create(
                merchid=acquirer_id.cconnect_merchant_account,
                account=post.get('account'),
                name=post.get('name'),
                expiry=post.get('expiry'),
            )
            if result and result.get('respcode') == '09':
                token = request.env['payment.token'].sudo().create({
                    'name': post.get('account', ''),
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
            return request.redirect('/my/payment/card')
        return request.redirect('/my/payment/card')

    @http.route(['/my/payment/tokens/delete/<model("payment.token"):mytoken>'], type='http', auth="user", website=True)
    def portal_my_payment_tokens_delete(self, mytoken=None, **kw):
        if mytoken:
            mytoken.active = False
        return request.redirect("/my/payment/card")

    @http.route(['/my/payment/card', '/my/payment/card/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_payment_tokens_card(self, page=1, date_begin=None, date_end=None, sortby=None, **kw):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        payment_token_obj = request.env['payment.token'].sudo()
        domain = [('partner_id', '=', partner.id)]
        searchbar_sortings = {
            'date': {'label': _('Date'), 'order': 'create_date desc'},
        }
        # default sortby order
        if not sortby:
            sortby = 'date'
        if date_begin and date_end:
            domain += [('create_date', '>', date_begin), ('create_date', '<=', date_end)]
        # count for pager
        payment_token_count = payment_token_obj.search_count(domain)
        # make pager
        pager = portal_pager(
            url="/my/payment/card",
            url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby},
            total=payment_token_count,
            page=page,
            step=self._items_per_page
        )
        # search the count to display, according to the pager data
        payment_tokens = payment_token_obj.search(domain, limit=self._items_per_page, offset=pager['offset'])
        request.session['my_gogpvehicle_history'] = payment_tokens.ids[:100]

        values.update({
            'date': date_begin,
            'payment_tokens': payment_tokens.sudo(),
            'page_name': 'mypayment',
            'pager': pager,
            'default_url': '/my/payment/card',
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
        })
        return request.render("payment_cardconnect_all_cr.portal_my_payment_tokens", values)