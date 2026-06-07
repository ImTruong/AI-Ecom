def category_to_dict(category):
    return {
        'id': category.id,
        'name': category.name,
        'slug': category.slug,
        'description': category.description,
        'icon': category.icon,
    }


def attribute_to_dict(attribute):
    return {
        'id': attribute.id,
        'name': attribute.name,
        'slug': attribute.slug,
        'values': [
            {'id': value.id, 'value': value.value, 'slug': value.slug}
            for value in attribute.values.all()
        ],
    }


def product_to_dict(product):
    return product.to_dict()


def variant_stock_to_dict(variant):
    return {'variant_id': variant.id, 'stock': variant.stock}

