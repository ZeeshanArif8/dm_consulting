odoo.define('payment_cardconnect_cr.payment_cardconnect_cr', function(require) {
    "use strict";

    var ajax = require('web.ajax');
    var core = require('web.core');
    var Dialog = require("web.Dialog");

    var _t = core._t;
    var qweb = core.qweb;

    $(document).ready(function() {
        var $modal;
        $('#o_payment_form_pay').on('click', function(ev) {
            // we retrieve the payment form
            var parent_form = ev.target.form;
            // then the checked radio
            var checked_radio = $('input[type="radio"]:checked', parent_form);
            // check if there's one checked radio
            if (checked_radio.length != 1) {
                return;
            }
            // if there's a checked radio, we retrieve the usefull data
            var acquirer_id = checked_radio.data('acquirerId');
            var provider = checked_radio.data('provider');
            var is_form_payment = checked_radio.data('form-payment') === "True";
            
            // now we check if the user has clicked on stripe radio button and wants to pay via the checkout form
            if (provider != "cardconnect" || is_form_payment !== true) {
                return;
            }

            var temp = 0;
            var loader = "<div class='cardconnect_payment_loder' style='display:none;'></div>";
            $('.o_payment_form').after(loader);

            if (temp == 0) {
                var amount = $('#cardconnect-checkout').find('input[name="amount"]').val();
                temp = 1;

                $('.cardconnect_payment_loder').show();
                if (!$modal) {
                    ajax.jsonRpc("/cardconnect/modal", 'call', {}).then(function(cardconnect_modal) {
                        $modal = $(cardconnect_modal);
                        
                        $('#o_payment_form_pay').hide();
                        $('#o_payment_form_pay').after($modal);

                        $('#myModal').modal('show');
                        // important part for create tx
                        create_draft_transaction();
                    });
                }
                return false;
            }
        });

        function create_draft_transaction() {
            var $payment_method = $('#payment_method');
            var $checked_radio = $payment_method.find('input[type="radio"]:checked');
            var acquirer_id = get_acquirer_id_from_radio($checked_radio);
            var $tx_url = $payment_method.find('input[name="prepare_tx_url"]');
            if ($checked_radio.length === 1) {
                $checked_radio = $checked_radio[0];
                if ($tx_url.length === 1) {
                    return ajax.jsonRpc($tx_url[0].value, 'call', {
                        'acquirer_id': parseInt(acquirer_id),
                    }).then(function (result) {
                        if (result) {
                            $('#payment_data').html(result);
                        }

                        else {
                            payment_display_error(
                                _t('Server Error'),
                                _t("We are not able to redirect you to the payment form.")
                            );
                        }
                    });
                } else {
                    // we append the form to the body and send it.
                    payment_display_error(
                        _t("Cannot set-up the payment"),
                        _t("We're unable to process your payment.")
                    );
                }
            } else {
                payment_display_error(
                    _t('No payment method selected'),
                    _t('Please select a payment method.')
                );
            }
        }

        function is_new_payment_radio(element) {
            return $(element).data('s2s-payment') === 'True';
        }

        function is_form_payment_radio(element) {
            return $(element).data('form-payment') === 'True';
        }

        function get_acquirer_id_from_radio(element) {
            return $(element).data('acquirer-id');
        }

        function payment_display_error(title, message) {
            var $payment_method = $('#payment_method');
            var $checked_radio = $payment_method.find('input[type="radio"]:checked'),
                acquirer_id = get_acquirer_id_from_radio($checked_radio[0]);

            var $acquirer_form;
            if (is_new_payment_radio($checked_radio[0])) {
                $acquirer_form = $payment_method.find('#o_payment_add_token_acq_' + acquirer_id);
            }
            else if (is_form_payment_radio($checked_radio[0])) {
                $acquirer_form = $payment_method.find('#o_payment_form_acq_' + acquirer_id);
            }

            if ($checked_radio.length === 0) {
                payment_dialog_message(title, message);
            } else {
                $('#payment_error').remove();
                var message_result = '<div class="alert alert-danger mb4" id="payment_error">';
                if (title != '') {
                    message_result = message_result + '<b>' + _.str.escapeHTML(title) + ':</b></br>';
                }
                message_result = message_result + _.str.escapeHTML(message) + '</div>';
                $acquirer_form.append(message_result);
            }
        }

        function payment_dialog_message(title, message) {
            return new Dialog(null, {
                title: _t('Error: ') + _.str.escapeHTML(title),
                size: 'medium',
                $content: "<p>" + (_.str.escapeHTML(message) || "") + "</p>" ,
                buttons: [
                {text: _t('Ok'), close: true}]}).open();
        }

        var $payment = $("#payment_method");
        $payment.on("click", "input[name='pm_id']", function(ev) {
            var provider = $(this).attr('data-provider');
            if (provider !== "cardconnect" && ($modal)) {
                $modal.hide();
                $('#o_payment_form_pay').show();
                return;
            } else if (provider === "cardconnect" && ($modal)) {
                $modal.show();
                $('#o_payment_form_pay').hide();
                return;
            }
        });
    });
});