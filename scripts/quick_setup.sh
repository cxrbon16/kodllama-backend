#!/bin/bash

echo "======================================"
echo "🚀 PlanLLaMA Quick Setup"
echo "======================================"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check Python version
echo -e "\n${YELLOW}Checking Python version...${NC}"
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | cut -d ' ' -f 2 | cut -d '.' -f 1,2)
    echo -e "${GREEN}✓ Python $PYTHON_VERSION found${NC}"
else
    echo -e "${RED}✗ Python 3 not found. Please install Python 3.10+${NC}"
    exit 1
fi

# Create virtual environment
echo -e "\n${YELLOW}Creating virtual environment...${NC}"
python3 -m venv venv
echo -e "${GREEN}✓ Virtual environment created${NC}"

# Activate virtual environment
echo -e "\n${YELLOW}Activating virtual environment...${NC}"
source venv/bin/activate
echo -e "${GREEN}✓ Virtual environment activated${NC}"

# Install dependencies
echo -e "\n${YELLOW}Installing dependencies...${NC}"
pip install --upgrade pip
pip install -r requirements.txt
echo -e "${GREEN}✓ Dependencies installed${NC}"

# Check PostgreSQL
echo -e "\n${YELLOW}Checking PostgreSQL...${NC}"
if command -v psql &> /dev/null; then
    echo -e "${GREEN}✓ PostgreSQL found${NC}"
else
    echo -e "${RED}✗ PostgreSQL not found${NC}"
    echo "Please install PostgreSQL 14+ and create a database:"
    echo "  CREATE DATABASE planllama_db;"
    exit 1
fi

# Setup environment file
echo -e "\n${YELLOW}Setting up environment variables...${NC}"
if [ ! -f .env ]; then
    cp .env.example .env
    echo -e "${GREEN}✓ .env file created${NC}"
    echo -e "${YELLOW}⚠ Please edit .env file with your configurations${NC}"
else
    echo -e "${YELLOW}ℹ .env file already exists${NC}"
fi

# Initialize database
echo -e "\n${YELLOW}Do you want to initialize the database? (y/n)${NC}"
read -r response
if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]];
then
    echo -e "${YELLOW}Initializing database...${NC}"
    python setup.py
    echo -e "${GREEN}✓ Database initialized${NC}"
    
    echo -e "\n${YELLOW}Do you want to add seed data? (y/n)${NC}"
    read -r seed_response
    if [[ "$seed_response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        python seed_data.py
        echo -e "${GREEN}✓ Seed data added${NC}"
    fi
fi

echo -e "\n======================================"
echo -e "${GREEN}✅ Setup Complete!${NC}"
echo -e "======================================\n"
echo "Next steps:"
echo "1. Edit .env file with your configurations"
echo "2. Start the server: python app.py"
echo "3. Test API: curl http://localhost:5000/health"
echo ""
echo "Happy coding! 🎉"
