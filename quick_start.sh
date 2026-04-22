#!/bin/bash
# MASTER QUICK START SCRIPT - ONE CLICK SETUP (AI & GRAPH VERSION)

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}🚀 TRUONGSHOP AI-DRIVEN MICROSERVICES INITIALIZER${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# 0. Check for API KEY
if [ ! -f .env ]; then
    echo -e "${YELLOW}Warning: .env file not found. Creating from .env.example...${NC}"
    cp .env.example .env
fi

# Ask user for API Key if not present
if grep -q "your-gemini-api-key-here" .env; then
    echo -e "${BLUE}AI CHATBOT CONFIGURATION:${NC}"
    echo -ne "${YELLOW}If you have a Google Gemini API Key, enter it now (or press Enter to skip): ${NC}"
    read api_key
    if [ ! -z "$api_key" ]; then
        sed -i '' "s/GEMINI_API_KEY=your-gemini-api-key-here/GEMINI_API_KEY=$api_key/" .env
        echo -e "${GREEN}API Key added! Chatbot will use real LLM responses.${NC}"
    else
        echo -e "${YELLOW}Skipping API Key. Chatbot will use high-quality local templates.${NC}"
    fi
fi

# 1. Start Containers
echo -e "${YELLOW}Step 1: Building and starting all containers...${NC}"
docker-compose up -d --build

echo -e "${BLUE}Waiting for services to be ready (30s)...${NC}"
sleep 30

# 2. Database Migrations
echo -e "${YELLOW}Step 2: Running Database Migrations...${NC}"
django_services=("auth-service" "customer-service" "product-service" "cart-service" "order-service" "payment-service" "voucher-service" "rating-service" "supplier-service" "tracking-service")

for service in "${django_services[@]}"; do
    echo "  - Migrating $service..."
    docker-compose exec -T $service python manage.py migrate --noinput || true
done

# 3. Knowledge Graph Population (Neo4j)
echo -e "${GREEN}Step 3: Populating Neo4j Knowledge Graph (KB)...${NC}"
docker-compose exec -T knowledge-service python importer.py

# 4. Final Summary
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}🎉 ALL SYSTEMS ONLINE & AI READY!${NC}"
echo -e "🌐 Frontend:    http://localhost:8000"
echo -e "📊 Knowledge:   http://localhost:7474 (Neo4j)"
echo -e "🤖 AI Chatbot:  Active in UI (Bottom-Right)"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
