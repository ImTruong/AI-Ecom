#!/bin/bash
# MASTER QUICK START SCRIPT - ONE CLICK SETUP (AI & GRAPH VERSION)

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}🚀 TRUONGSHOP AI-DRIVEN MICROSERVICES INITIALIZER${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# Detect Docker Compose version
if docker compose version > /dev/null 2>&1; then
    DOCKER_CMD="docker compose"
    echo -e "${GREEN}Using Docker Compose V2${NC}"
else
    DOCKER_CMD="docker-compose"
    echo -e "${YELLOW}Using Docker Compose V1 (Legacy)${NC}"
fi

# 0. Check for API KEY
if [ ! -f .env ]; then
    echo -e "${YELLOW}Warning: .env file not found. Creating from .env.example...${NC}"
    cp .env.example .env
fi

# Ask user for API Key if not present
if grep -q "your-freellm-api-key-here" .env; then
    echo -e "${BLUE}AI CHATBOT CONFIGURATION:${NC}"
    echo -ne "${YELLOW}If you have a FreeLLM API Key, enter it now (or press Enter to skip): ${NC}"
    read api_key
    if [ ! -z "$api_key" ]; then
        # Fix sed command for Linux compatibility
        sed -i "s/FREELLM_API_KEY=your-freellm-api-key-here/FREELLM_API_KEY=$api_key/" .env
        echo -e "${GREEN}API Key added! Chatbot will use real LLM responses.${NC}"
    else
        echo -e "${YELLOW}Skipping API Key. Chatbot will use high-quality local templates.${NC}"
    fi
fi

# 1. Start Containers
echo -e "${YELLOW}Step 1: Cleaning up and starting all containers...${NC}"
# Run down first to fix "ContainerConfig" and "ImageNotFound" inconsistencies
$DOCKER_CMD down --remove-orphans

echo -e "${YELLOW}Building and starting services...${NC}"
$DOCKER_CMD up -d --build

echo -e "${BLUE}Waiting for services to be ready (60s)...${NC}"
sleep 60

# Check if user-service is healthy
echo -e "${BLUE}Checking user-service health...${NC}"
for i in {1..10}; do
    if curl -s http://localhost:8001/api/auth/token/verify/ > /dev/null 2>&1 || curl -s http://localhost:8000/api/auth/token/verify/ > /dev/null 2>&1; then
        echo -e "${GREEN}User service is ready!${NC}"
        break
    fi
    echo "  Attempt $i/10 - waiting for user-service..."
    sleep 5
done

# 2. Database Migrations
echo -e "${YELLOW}Step 2: Running Database Migrations...${NC}"
django_services=("user-service" "product-service" "cart-service" "order-service" "payment-service" "voucher-service" "rating-service" "supplier-service" "tracking-service")

for service in "${django_services[@]}"; do
    echo "  - Migrating $service..."
    $DOCKER_CMD exec -T $service python manage.py migrate --noinput || echo -e "${RED}Failed to migrate $service${NC}"
done

# 3. Seed initial data (Products, Vouchers, Default Users)
echo -e "${GREEN}Step 3: Seeding data (Products, Vouchers, Default Users)...${NC}"
$DOCKER_CMD exec -T product-service python seed_products.py || echo -e "${RED}Failed to seed products${NC}"
$DOCKER_CMD exec -T voucher-service python seed_vouchers.py || echo -e "${RED}Failed to seed vouchers${NC}"
$DOCKER_CMD exec -T user-service python seed_roles.py || echo -e "${RED}Failed to seed RBAC roles${NC}"
$DOCKER_CMD exec -T user-service python seed_users.py || echo -e "${RED}Failed to seed default users${NC}"

# 4. Vector Index (Qdrant)
echo -e "${GREEN}Step 4: Building vector index for products...${NC}"
$DOCKER_CMD --profile manual run --rm --build vector-service || echo -e "${RED}Failed to build vector index${NC}"

# 5. Knowledge Graph Population (Neo4j)
echo -e "${GREEN}Step 5: Populating Neo4j Knowledge Graph (KB)...${NC}"
$DOCKER_CMD exec -T knowledge-service python importer.py || echo -e "${RED}Failed to populate knowledge graph${NC}"

# 6. Final Summary
echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}🎉 ALL SYSTEMS ONLINE & AI READY!${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${YELLOW}📱 APPLICATION${NC}"
echo -e "   🌐 Frontend:       http://localhost:8000"
echo -e "   🔐 Admin Panel:    http://localhost:8000/staff/login/"
echo ""
echo -e "${YELLOW}🗄️  DATABASES & SERVICES${NC}"
echo -e "   📊 Neo4j Browser:  http://localhost:7474/browser/"
echo -e "                      (No auth required - click 'Connect')"
echo -e "   🔍 Qdrant API:     http://localhost:6333/"
echo -e "   📮 RabbitMQ Mgmt: http://localhost:15672/ (admin/admin123)"
echo ""
echo -e "${YELLOW}👥 DEFAULT ACCOUNTS${NC}"
echo -e "   👤 Customer:       client@example.com / client123"
echo -e "   👷 Staff:          staff@example.com / staff123"
echo -e "   🛡️  Admin:          admin@example.com / admin123"
echo ""
echo -e "${YELLOW}⚠️  IMPORTANT NOTES${NC}"
echo -e "   • Neo4j: Wait 10-15s after opening, then click 'Connect'"
echo -e "   • Qdrant: Use API endpoint http://localhost:6333/collections"
echo -e "   • All services need ~60s to fully start"
echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
