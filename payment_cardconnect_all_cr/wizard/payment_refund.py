# -*- coding: utf-8 -*-

from odoo import api, models, fields, _
from odoo.exceptions import UserError
from .. import cardconnect

class SalePaymentRefund(models.TransientModel):
    _name = "sale.payment.refund"
    _description = "Sale Payment Refund"

    payment_transaction_id = fields.Many2one('payment.transaction' ,string='Payment Transaction',required=True)
    type = fields.Selection([('refund','Refund'),('void','Void')], string='Type')
    amount_type = fields.Selection([('full','Full Payment'),('partial','Partial Payment')], string='Amount Type', default='full',required=True)
    amount = fields.Float(string='Amount')

    @api.onchange('amount_type')
    def _onchange_amount_type(self):
        for record in self:
            record.amount = record.payment_transaction_id.amount - record.payment_transaction_id.refund_amount

    def refund(self):
        tra_amount = self.payment_transaction_id.amount - self.payment_transaction_id.refund_amount
        if self.payment_transaction_id and self.amount and self.payment_transaction_id.acquirer_id:
            if self.amount_type == 'partial' and self.amount >= tra_amount:
                raise UserError(_("If you want to do partial then please set less amount then original amount "))
            else:
                cardconnect.username = self.payment_transaction_id.acquirer_id.cconnect_user
                cardconnect.password = self.payment_transaction_id.acquirer_id.cconnect_pwd
                cardconnect.base_url = self.payment_transaction_id.acquirer_id.cconnect_url
                cardconnect.debug = True
                if self.type == 'refund':
                    result = cardconnect.Refund.create(
                        retref=self.payment_transaction_id.acquirer_reference,
                        merchid = self.payment_transaction_id.acquirer_id.cconnect_merchant_account,
                        amount = str(self.amount)
                    )
                    if result and result.get('respcode') == '00' and result.get('resptext') == 'Approval':
                        self.payment_transaction_id.state = self.amount_type == 'full' and 'refund' or 'partial_refund'
                        if self.payment_transaction_id.payment_id and self.payment_transaction_id.payment_id.state == 'posted':
                            self.payment_transaction_id.refund_amount = self.payment_transaction_id.refund_amount + self.amount
                            if self.amount_type == 'full':
                                self.payment_transaction_id.payment_id.action_draft()
                                self.payment_transaction_id.payment_id.action_cancel()
                            else:
                                self.payment_transaction_id.payment_id.action_draft()
                                self.payment_transaction_id.payment_id.amount = tra_amount - self.amount
                                self.payment_transaction_id.payment_id.action_post()
                if self.type == 'void':
                    result = cardconnect.Void.create(
                        retref=self.payment_transaction_id.acquirer_reference,
                        merchid=self.payment_transaction_id.acquirer_id.cconnect_merchant_account,
                        amount=str(self.amount)
                    )
                    if result and result.get('respcode') == '00' and result.get('resptext') == 'Approval':
                        self.payment_transaction_id.state = self.amount_type == 'full' and 'void' or 'partial_void'
                        if self.payment_transaction_id.payment_id and self.payment_transaction_id.payment_id.state == 'posted':
                            self.payment_transaction_id.refund_amount = self.payment_transaction_id.refund_amount + self.amount
                            if self.amount_type == 'full':
                                self.payment_transaction_id.payment_id.action_draft()
                                self.payment_transaction_id.payment_id.action_cancel()
                            else:
                                self.payment_transaction_id.payment_id.action_draft()
                                self.payment_transaction_id.payment_id.amount = tra_amount - self.amount
                                self.payment_transaction_id.payment_id.action_post()

        else:
            raise UserError(_("Order/Transaction/Amount not set"))

