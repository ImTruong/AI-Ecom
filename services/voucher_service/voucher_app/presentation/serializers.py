def voucher_to_dict(voucher):
    return voucher.to_dict()


def voucher_validation_to_dict(voucher, order_amount, discount):
    return {
        'id': voucher.id,
        'code': voucher.code,
        'discount_applied': float(discount),
        'new_total': float(order_amount) - float(discount),
    }

