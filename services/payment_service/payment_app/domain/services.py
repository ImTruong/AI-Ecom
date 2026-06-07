def payment_status_for_method(payment_method: str):
    return 'pending' if payment_method == 'cod' else 'completed'


def is_online_method(payment_method: str):
    return payment_method != 'cod'

