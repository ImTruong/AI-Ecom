from .exceptions import SupplierValidationError


def validate_supplier_payload(payload):
    missing = [field for field in ['name', 'email', 'phone', 'address'] if not payload.get(field)]
    if missing:
        raise SupplierValidationError(f"Missing required fields: {', '.join(missing)}")

