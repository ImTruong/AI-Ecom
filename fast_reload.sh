#!/bin/bash
# FAST RELOAD SCRIPT (Developer Only)

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}♻️ RELOADING AI MICROSERVICES...${NC}"

# Detect Docker Compose version
if docker compose version > /dev/null 2>&1; then
    DOCKER_CMD="docker compose"
else
    DOCKER_CMD="docker-compose"
fi

# Re-build only the updated services
$DOCKER_CMD up -d --build api-gateway recommendation-service tracking-service chatbot-service

# Rebuild vector index for updated search/recommendations
echo -e "${GREEN}🧠 Rebuilding product vectors...${NC}"
$DOCKER_CMD --profile manual run --rm --build vector-service || echo "Vector index rebuild failed"

echo -e "${GREEN}✅ RELOAD COMPLETE!${NC}"
echo -e "🌐 http://localhost:8000"
