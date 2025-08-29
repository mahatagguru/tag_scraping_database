#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Testing Docker Setup ===${NC}"

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running. Please start Docker and try again.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Docker is running${NC}"

# Check if docker-compose is available
if ! command -v docker-compose >/dev/null 2>&1; then
    echo -e "${RED}❌ docker-compose is not available. Please install it and try again.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ docker-compose is available${NC}"

# Check if required files exist
required_files=(
    "docker-compose.yml"
    "Dockerfile"
    "bin/run.sh"
    "bin/run_pipeline.sh"
    "env.example"
)

for file in "${required_files[@]}"; do
    if [[ -f "$file" ]]; then
        echo -e "${GREEN}✅ $file exists${NC}"
    else
        echo -e "${RED}❌ $file is missing${NC}"
        exit 1
    fi
done

# Check if scripts are executable
if [[ -x "bin/run.sh" && -x "bin/run_pipeline.sh" ]]; then
    echo -e "${GREEN}✅ Scripts are executable${NC}"
else
    echo -e "${RED}❌ Scripts are not executable${NC}"
    exit 1
fi

# Test Docker build (without running)
echo -e "${BLUE}Testing Docker build...${NC}"
if docker-compose build --no-cache; then
    echo -e "${GREEN}✅ Docker build successful${NC}"
else
    echo -e "${RED}❌ Docker build failed${NC}"
    exit 1
fi

# Test docker-compose config
echo -e "${BLUE}Testing docker-compose configuration...${NC}"
if docker-compose config >/dev/null; then
    echo -e "${GREEN}✅ docker-compose configuration is valid${NC}"
else
    echo -e "${RED}❌ docker-compose configuration is invalid${NC}"
    exit 1
fi

echo -e "${BLUE}=== Docker Setup Test Complete ===${NC}"
echo -e "${GREEN}✅ All tests passed! Your Docker setup is ready.${NC}"
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo "1. Copy env.example to .env and configure your settings"
echo "2. Run: docker-compose up -d"
echo "3. Check logs: docker-compose logs -f scraper"
echo ""
echo -e "${BLUE}For more information, see DOCKER_README.md${NC}"
