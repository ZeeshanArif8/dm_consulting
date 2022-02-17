# -*- coding: utf-8 -*-
# Part of Odoo Module Developed by Candidroot Solutions Pvt. Ltd.
# See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from .. import cardconnect

class AccountMoveLine(models.Model):
    _inherit = "account.move.line"
    
    is_cardconnect_fees_line = fields.Boolean('Card Connect Fees Line')

class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    is_cardconnect_fees_line = fields.Boolean('Card Connect Fees Line')
    
class SaleOrder(models.Model):
    _inherit = "sale.order"

    payment_token_count = fields.Integer('Count Payment Token', compute='_compute_payment_token_count')

    def _create_payment_transaction(self, vals):
        # Ensure the currencies are the same.
        currency = self[0].pricelist_id.currency_id
        if any(so.pricelist_id.currency_id != currency for so in self):
            raise ValidationError(_('A transaction can\'t be linked to sales orders having different currencies.'))

        # Ensure the partner are the same.
        partner = self[0].partner_id
        if any(so.partner_id != partner for so in self):
            raise ValidationError(_('A transaction can\'t be linked to sales orders having different partners.'))

        # Try to retrieve the acquirer. However, fallback to the token's acquirer.
        acquirer_id = vals.get('acquirer_id')
        acquirer = False
        payment_token_id = vals.get('payment_token_id')

        if payment_token_id:
            payment_token = self.env['payment.token'].sudo().browse(payment_token_id)
            # Check payment_token/acquirer matching or take the acquirer from token
            if acquirer_id:
                acquirer = self.env['payment.acquirer'].browse(acquirer_id)
                if payment_token and payment_token.acquirer_id != acquirer:
                    raise ValidationError(_('Invalid token found! Token acquirer %s != %s') % (
                        payment_token.acquirer_id.name, acquirer.name))
                if payment_token and payment_token.partner_id != partner:
                    raise ValidationError(_('Invalid token found! Token partner %s != %s') % (
                        payment_token.partner.name, partner.name))
            else:
                acquirer = payment_token.acquirer_id

        # Check an acquirer is there.
        if not acquirer_id and not acquirer:
            raise ValidationError(_('A payment acquirer is required to create a transaction.'))

        if not acquirer:
            acquirer = self.env['payment.acquirer'].browse(acquirer_id)

        if acquirer and acquirer.provider == 'cardconnect':
            acquirer_fees = acquirer.cardconnect_compute_fees(sum(self.mapped('amount_total')), currency, partner.country_id.id)
            if acquirer_fees:
                for order in self:
                    fees_line = order.order_line.filtered(lambda line: line.is_cardconnect_fees_line)
                    fees_product = self.env.ref('payment_cardconnect_all_cr.product_cardconnect_fees_line')
                    if fees_line:
                        fees_line.write({'price_unit': acquirer_fees})
                    else:
                        val = {
                            'name': fees_product.name,
                            'product_id': fees_product.id,
                            'product_uom_qty': 1,
                            'price_unit': acquirer_fees,
                            'is_cardconnect_fees_line': True,
                        }
                        order.write({'order_line': [(0, 0, val)]})
        return super(SaleOrder, self)._create_payment_transaction(vals)

    def _compute_payment_token_count(self):
        for r in self:
            token = self.env['payment.token'].sudo().search([('partner_id','in',r.partner_id.ids)])
            r.payment_token_count = len(token)

    def partner_payment_token(self):
        context = dict(self._context)
        context.update({'search_default_partner_id': self.partner_id.id,'create':False,'edit':False})
        token = self.env['payment.token'].sudo().search([('partner_id','in',self.partner_id.ids)])
        action = {
            'name': _('Payment Token'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'payment.token',
            'context': context,
        }
        if len(token) == 1:
            action.update({
                'view_mode': 'form',
                'res_id': token.id,
            })
        elif len(token) > 1:
            action.update({
                'view_mode': 'tree,form',
                'domain': [('id', 'in', token.ids)],
            })
        return action

    def create_new_payment_token(self):
        context = dict(self._context)
        context.update({'default_partner_id': self.partner_id.id})
        view = self.env.ref('payment_cardconnect_all_cr.view_sale_payment_token_form')
        return {
            'name': _('Payment Token'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'sale.payment.token',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'context': context
        }

    @api.depends('transaction_ids','transaction_ids.state')
    def _compute_sale_payment_refund(self):
        val = False
        for order in self:
            transaction = order.transaction_ids.filtered(lambda x: x.state in ['done','partial_refund','partial_void'] and x.acquirer_id.provider == 'cardconnect')
            if transaction:
                val = True
            order.is_sale_payment_refund = val

    is_sale_payment_refund = fields.Boolean(compute="_compute_sale_payment_refund",store=True)

    def create_sale_payment_refund(self):
        transaction = self.transaction_ids.filtered(lambda x: x.state in ['done','partial_refund','partial_void'] and x.acquirer_id.provider == 'cardconnect')
        if transaction:
            cardconnect.username = transaction.acquirer_id.cconnect_user
            cardconnect.password = transaction.acquirer_id.cconnect_pwd
            cardconnect.base_url = transaction.acquirer_id.cconnect_url
            cardconnect.debug = True
            result = cardconnect.Inquire.get(
                merchid=transaction.acquirer_id.cconnect_merchant_account,
                retref=transaction.acquirer_reference,
            )
            context = dict(self._context)
            if result and result.get('respcode') == '00' and result.get('setlstat') in ['Authorized','Queued for Capture']:
                context.update({'default_type': 'void'})
            elif result and result.get('respcode') == '00' and result.get('setlstat') == 'refundable':
                context.update({'default_type': 'refund'})
            else:
                raise UserError(_("You can not do void or refund for this transaction"))
            view = self.env.ref('payment_cardconnect_all_cr.view_sale_payment_refund_form')
            context.update({'default_payment_transaction_id': transaction.id})
            return {
                'name': _('Payment Refund'),
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'sale.payment.refund',
                'views': [(view.id, 'form')],
                'view_id': view.id,
                'target': 'new',
                'context': context
            }
        else:
            raise UserError(_("Order/Transaction not done"))

class AccountMove(models.Model):
    _inherit = "account.move"

    payment_token_count = fields.Integer('Count Payment Token', compute='_compute_payment_token_count')

    def _create_payment_transaction(self, vals):
        # Ensure the currencies are the same.
        currency = self[0].currency_id
        if any(inv.currency_id != currency for inv in self):
            raise ValidationError(_('A transaction can\'t be linked to invoices having different currencies.'))

        # Ensure the partner are the same.
        partner = self[0].partner_id
        if any(inv.partner_id != partner for inv in self):
            raise ValidationError(_('A transaction can\'t be linked to invoices having different partners.'))

        # Try to retrieve the acquirer. However, fallback to the token's acquirer.
        acquirer_id = vals.get('acquirer_id')
        acquirer = None
        payment_token_id = vals.get('payment_token_id')

        if payment_token_id:
            payment_token = self.env['payment.token'].sudo().browse(payment_token_id)

            # Check payment_token/acquirer matching or take the acquirer from token
            if acquirer_id:
                acquirer = self.env['payment.acquirer'].browse(acquirer_id)
                if payment_token and payment_token.acquirer_id != acquirer:
                    raise ValidationError(_('Invalid token found! Token acquirer %s != %s') % (
                        payment_token.acquirer_id.name, acquirer.name))
                if payment_token and payment_token.partner_id != partner:
                    raise ValidationError(_('Invalid token found! Token partner %s != %s') % (
                        payment_token.partner.name, partner.name))
            else:
                acquirer = payment_token.acquirer_id

        # Check an acquirer is there.
        if not acquirer_id and not acquirer:
            raise ValidationError(_('A payment acquirer is required to create a transaction.'))

        if not acquirer:
            acquirer = self.env['payment.acquirer'].browse(acquirer_id)

        if acquirer and acquirer.provider == 'cardconnect':
            acquirer_fees = acquirer.cardconnect_compute_fees(sum(self.mapped('amount_residual')), currency, partner.country_id.id)
            if acquirer_fees:
                for invoice in self:
                    fees_line = invoice.invoice_line_ids.filtered(lambda line: line.is_cardconnect_fees_line)
                    fees_product = self.env.ref('payment_cardconnect_all_cr.product_cardconnect_fees_line')
                    if fees_line:
                        fees_line.write({'price_unit': acquirer_fees})
                    else:
                        val = {
                            'name': fees_product.name,
                            'product_id': fees_product.id,
                            'quantity': 1,
                            'price_unit': acquirer_fees,
                            'is_cardconnect_fees_line': True,
                            'account_id': fees_product.property_account_income_id.id,
                        }
                        invoice.write({'invoice_line_ids': [(0, 0, val)]})
        return super(AccountMove, self)._create_payment_transaction(vals)

    def _compute_payment_token_count(self):
        for r in self:
            token = self.env['payment.token'].sudo().search([('partner_id', 'in', r.partner_id.ids)])
            r.payment_token_count = len(token)

    def partner_payment_token(self):
        context = dict(self._context)
        context.update({'search_default_partner_id': self.partner_id.id, 'create': False, 'edit': False})
        token = self.env['payment.token'].sudo().search([('partner_id', 'in', self.partner_id.ids)])
        action = {
            'name': _('Payment Token'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'payment.token',
            'context': context,
        }
        if len(token) == 1:
            action.update({
                'view_mode': 'form',
                'res_id': token.id,
            })
        elif len(token) > 1:
            action.update({
                'view_mode': 'tree,form',
                'domain': [('id', 'in', token.ids)],
            })
        return action

    def create_new_payment_token(self):
        context = dict(self._context)
        context.update({'default_partner_id': self.partner_id.id})
        view = self.env.ref('payment_cardconnect_all_cr.view_sale_payment_token_form')
        return {
            'name': _('Payment Token'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'sale.payment.token',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'context': context
        }

class ResPartner(models.Model):
    _inherit = "res.partner"

    def create_new_payment_token(self):
        context = dict(self._context)
        context.update({'default_partner_id': self.id})
        view = self.env.ref('payment_cardconnect_all_cr.view_sale_payment_token_form')
        return {
            'name': _('Payment Token'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'sale.payment.token',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'context': context
        }