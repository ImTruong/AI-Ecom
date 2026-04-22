#!/bin/bash
# FAST RELOAD SCRIPT (Developer Only)

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}♻️ RELOADING AI MICROSERVICES...${NC}"

# Re-build specific services if needed
docker-compose up -d --build api-gateway chatbot-service knowledge-service product-service

# Run migrations (just in case)
docker-compose exec -T api-gateway python manage.py migrate --noinput

# Refresh Knowledge Graph
echo -e "${GREEN}📊 Refreshing Knowledge Graph Data...${NC}"
docker-compose exec -T knowledge-service python importer.py

echo -e "${GREEN}✅ RELOAD COMPLETE!${NC}"
echo -e "🌐 http://localhost:8000"
