odoo.define('payment_cardconnect_all_cr.portal', function (require) {
    'use strict';

    var core = require('web.core');
    var publicWidget = require('web.public.widget');
    var _t = core._t;
    var Dialog = require('web.Dialog');

    $(document).ready(function(){
        var delete_id;
        $(".delete_button_id").on('click', function (ev) {
            $('#delete_paymentcard_model_id').modal('show');
            delete_id = window.location.origin+'/my/payment/tokens/delete/'+ev.currentTarget.previousElementSibling.value
            $("#delete_paymentcard_model_id a.delete-confirm").attr("href", delete_id);
        });
    });

    publicWidget.registry.portal_payment_tokens = publicWidget.Widget.extend({
        selector: '.payment_tokens_thead',

        init: function () {
            this._super.apply(this, arguments);
        },

        start: function () {
            var self = this;
            this._super.apply(this, arguments);
            $('.add_new_paymentcard').click(function(e){
                self._rpc({
                    route: '/my/payment/tokens/add',
                    params: {},
                }).then(function (tokens){
                    var $modal = $(tokens);
                    $modal.modal({backdrop: 'static', keyboard: false});
                    $modal.find('.modal-body > div').removeClass('container'); // retrocompatibility - REMOVE ME in master / saas-19
                    $modal.appendTo('body').modal();
                });
            });
        },
    });
});
