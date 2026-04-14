#!/bin/bash

# MASTER QUICK START SCRIPT - ONE CLICK SETUP
# This script initializes the entire project: Services, DBs, Seeds, and AI.

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}🚀 TRUONGSHOP AI-DRIVEN MICROSERVICES INITIALIZER${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# Step 0: Clean up
echo -e "${YELLOW}Step 0: Cleaning up existing environment...${NC}"
docker-compose down --remove-orphans
rm -f services/tracking_service/db.sqlite3

# Step 1: Build and start
echo -e "${BLUE}Step 1: Building and starting all containers...${NC}"
docker-compose up -d --build

echo -e "${YELLOW}Waiting for systems to stabilize (20s)...${NC}"
sleep 20

# Step 2: Migrations
echo -e "${BLUE}Step 2: Synchronizing Database Schemas...${NC}"
services=("auth-service" "customer-service" "product-service" "cart-service" "order-service" "payment-service" "voucher-service" "rating-service" "supplier-service" "tracking-service")

for service in "${services[@]}"; do
    echo "  - Migrating $service..."
    docker-compose exec -T $service python manage.py migrate --noinput
done

# Step 3: Master Seed
echo -e "${BLUE}Step 3: Populating Master Seed Data...${NC}"
db_containers=("auth_db" "customer_db" "product_db" "rating_db" "supplier_db")

for db_container in "${db_containers[@]}"; do
    service_prefix=$(echo $db_container | cut -d'_' -f1)
    echo "  - Seeding $db_container..."
    docker-compose exec -T $db_container psql -U ${service_prefix}_user -d ${service_prefix}_db < seed_data.sql > /dev/null 2>&1 || true
    
    # Run extra seeds for product service
    if [ "$db_container" == "product_db" ]; then
        docker-compose exec -T product_db psql -U product_user -d product_db < extra_seeds.sql > /dev/null 2>&1 || true
    fi
done

# Step 4: AI Vector Sync
echo -e "${BLUE}Step 4: Synchronizing AI Recommendation Engine (Vector Sync)...${NC}"
docker-compose --profile manual run --rm vector-service

echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}🎉 ALL SYSTEMS ONLINE & AI IS TRAINED!${NC}"
echo -e "🌐 Frontend: http://localhost:8000"
echo -e "📊 Tracking Stats: http://localhost:8010/api/tracking/stats/"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

echo -e "${YELLOW}Login info:${NC}"
echo "  Customer: customer@truongshop.com / password123"
echo "  Staff:    staff@truongshop.com / staffpass123"
echo ""
