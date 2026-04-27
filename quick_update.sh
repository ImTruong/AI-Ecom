#!/bin/bash

# Updated Quick Update Script - 12 Microservices Architecture
# This script rebuilds and restarts all services and runs migrations

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}🚀 Starting Quick Update process...${NC}"

# Detect Docker Compose version
if docker compose version > /dev/null 2>&1; then
    DOCKER_CMD="docker compose"
else
    DOCKER_CMD="docker-compose"
fi

# 1. Ensure all network, core infrastructure, and workers are up
$DOCKER_CMD up -d rabbitmq auth_db customer_db staff_db product_db cart_db order_db payment_db voucher_db rating_db supplier_db tracking_db auth-publisher customer-consumer
sleep 5

# 2. Rebuild and restart all microservices
echo "📦 Building and updating all microservices..."
$DOCKER_CMD up -d --build api-gateway auth-service customer-service product-service staff-service cart-service order-service payment-service voucher-service rating-service supplier-service tracking-service

# 3. Always check for migrations and apply them in all services
echo "📝 Checking for and applying database migrations..."
services=("auth-service" "customer-service" "product-service" "staff-service" "cart-service" "order-service" "payment-service" "voucher-service" "rating-service" "supplier-service" "tracking-service")

for service in "${services[@]}"; do
    if [ $($DOCKER_CMD ps -q $service) ]; then
        echo "  - Migrating $service..."
        $DOCKER_CMD exec -T $service python manage.py makemigrations || echo "No migrations for $service"
        $DOCKER_CMD exec -T $service python manage.py migrate || echo -e "${RED}Migration failed for $service${NC}"
    else
        echo "  - Skipping $service (not running)"
    fi
done

echo ""
echo -e "${GREEN}✅ QUICK UPDATE COMPLETE!${NC}"
echo -e "🌐 API Gateway:  http://localhost:8000"
echo -e "🌐 Tracking Stats: http://localhost:8000/api/tracking/stats/"

echo -e "${BLUE}🌱 Seeding Products, Vouchers & Default Users...${NC}"
$DOCKER_CMD exec -T product-service python seed_products.py || echo "Product seeding failed"
$DOCKER_CMD exec -T voucher-service python seed_vouchers.py || echo "Voucher seeding failed"
$DOCKER_CMD exec -T auth-service python seed_users.py || echo "User seeding failed"

echo -e "${BLUE}📊 Refreshing Knowledge Graph Data...${NC}"
$DOCKER_CMD exec -T knowledge-service python importer.py || echo "Knowledge import failed"

