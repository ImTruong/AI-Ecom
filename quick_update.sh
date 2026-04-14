#!/bin/bash

# Updated Quick Update Script - 12 Microservices Architecture
# This script rebuilds and restarts all services and runs migrations

set -e

echo "🚀 Starting Quick Update process..."

# 1. Ensure all network, core infrastructure, and workers are up
docker-compose up -d rabbitmq auth_db customer_db staff_db product_db cart_db order_db payment_db voucher_db rating_db supplier_db tracking_db auth-publisher customer-consumer
sleep 5

# 2. Rebuild and restart all microservices
echo "📦 Building and updating all microservices..."
docker-compose up -d --build api-gateway auth-service customer-service product-service staff-service cart-service order-service payment-service voucher-service rating-service supplier-service tracking-service

# 3. Always check for migrations and apply them in all services
echo "📝 Checking for and applying database migrations..."
services=("auth-service" "customer-service" "product-service" "staff-service" "cart-service" "order-service" "payment-service" "voucher-service" "rating-service" "supplier-service" "tracking-service")

for service in "${services[@]}"; do
    if [ $(docker-compose ps -q $service) ]; then
        echo "  - Migrating $service..."
        docker-compose exec -T $service python manage.py makemigrations
        docker-compose exec -T $service python manage.py migrate
    else
        echo "  - Skipping $service (not running)"
    fi
done

echo ""
echo "✅ QUICK UPDATE COMPLETE!"
echo "🌐 API Gateway:  http://localhost:8000"
echo "🌐 Tracking Stats: http://localhost:8000/api/tracking/stats/"
