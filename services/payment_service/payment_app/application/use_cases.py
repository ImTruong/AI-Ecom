from payment_app.domain.repositories import PaymentRepository


class PaymentUseCases:
    def __init__(self, repository: PaymentRepository):
        self.repository = repository

    def process_payment(self, payload):
        return self.repository.create_payment(payload)

    def get_payment_status(self, order_id):
        return self.repository.get_by_order(order_id)

    def list_payment_methods(self):
        return self.repository.list_methods()

    def list_payment_logs(self, payment_id):
        return self.repository.list_logs(payment_id)

