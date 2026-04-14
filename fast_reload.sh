#!/bin/bash

# Fast Reload Script - Only for Product, Tracking, and Gateway services
# This script rebuilds only the modified services and runs migrations

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🚀 Reloading updated services...${NC}"

# 1. Update infrastructure and Hard Reset Tracking if requested
echo "Checking core infrastructure..."
# Remove the sqlite file if it exists to force Postgres usage
rm -f services/tracking_service/db.sqlite3
docker-compose up -d product_db tracking_db rabbitmq qdrant

# 2. Rebuild and restart only the modified services
echo -e "${BLUE}📦 Rebuilding target services...${NC}"
docker-compose up -d --build product-service tracking-service api-gateway cart-service order-service recommendation-service

# 3. Synchronize migrations
echo -e "${BLUE}📝 Running migrations for updated services...${NC}"
services=("product-service" "tracking-service" "cart-service" "order-service")

for service in "${services[@]}"; do
    echo "  - Migrating $service..."
    docker-compose exec -T $service python manage.py makemigrations
    docker-compose exec -T $service python manage.py migrate
done

echo ""
echo -e "${GREEN}✅ RELOAD COMPLETE!${NC}"
echo "🌐 API Gateway: http://localhost:8000"
echo "🌐 Tracking Stats: http://localhost:8012/api/tracking/stats/"
