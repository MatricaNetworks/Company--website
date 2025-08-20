#!/bin/bash

# Matrica Networks - Start Server Script
# 
# This script starts the Matrica Networks cybersecurity website using Docker Compose
# with proper initialization, health checks, and logging.

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# ASCII Art Banner
echo -e "${CYAN}"
cat << "EOF"
 ███▄ ▄███▓ ▄▄▄      ▄▄▄█████▓ ██▀███   ██▓ ▄████▄   ▄▄▄      
▓██▒▀█▀ ██▒▒████▄    ▓  ██▒ ▓▒▓██ ▒ ██▒▓██▒▒██▀ ▀█  ▒████▄    
▓██    ▓██░▒██  ▀█▄  ▒ ▓██░ ▒░▓██ ░▄█ ▒▒██▒▒▓█    ▄ ▒██  ▀█▄  
▒██    ▒██ ░██▄▄▄▄██ ░ ▓██▓ ░ ▒██▀▀█▄  ░██░▒▓▓▄ ▄██▒░██▄▄▄▄██ 
▒██▒   ░██▒ ▓█   ▓██▒  ▒██▒ ░ ░██▓ ▒██▒░██░▒ ▓███▀ ░ ▓█   ▓██▒
░ ▒░   ░  ░ ▒▒   ▓▒█░  ▒ ░░   ░ ▒▓ ░▒▓░░▓  ░ ░▒ ▒  ░ ▒▒   ▓▒█░
░  ░      ░  ▒   ▒▒ ░    ░      ░▒ ░ ▒░ ▒ ░  ░  ▒     ▒   ▒▒ ░
░      ░     ░   ▒     ░        ░░   ░  ▒ ░░          ░   ▒   
       ░         ░  ░            ░      ░  ░ ░            ░  ░
                                           ░                  
        NETWORKS - Cybersecurity Solutions
EOF
echo -e "${NC}"

echo -e "${BLUE}🚀 Starting Matrica Networks Application...${NC}"
echo ""

# Function to print colored output
print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

# Check if Docker is installed and running
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker first."
    echo "Visit: https://docs.docker.com/get-docker/"
    exit 1
fi

if ! docker info &> /dev/null; then
    print_error "Docker is not running. Please start Docker first."
    exit 1
fi

print_status "Docker is available and running"

# Check if Docker Compose is available
if ! command -v docker-compose &> /dev/null; then
    if ! docker compose version &> /dev/null; then
        print_error "Docker Compose is not available. Please install Docker Compose."
        exit 1
    fi
    COMPOSE_CMD="docker compose"
else
    COMPOSE_CMD="docker-compose"
fi

print_status "Docker Compose is available"

# Create necessary directories for volume mounts
print_info "Creating data directories..."
mkdir -p data/{db,logs,storage,backups}
mkdir -p data/storage/{uploads,docs}

# Set proper permissions
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux: Set permissions for Docker user mapping
    chmod -R 755 data/
    print_status "Directory permissions set for Linux"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS: Set permissions
    chmod -R 755 data/
    print_status "Directory permissions set for macOS"
fi

# Check if containers are already running
if $COMPOSE_CMD ps | grep -q "matrica-app.*Up"; then
    print_warning "Matrica Networks is already running!"
    echo ""
    print_info "Current status:"
    $COMPOSE_CMD ps
    echo ""
    read -p "Do you want to restart the application? (y/N): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_info "Restarting application..."
        $COMPOSE_CMD restart
    else
        print_info "Application is already running. Use 'docker-compose logs -f' to view logs."
        exit 0
    fi
else
    # Stop any existing containers
    if $COMPOSE_CMD ps -q | grep -q .; then
        print_info "Stopping existing containers..."
        $COMPOSE_CMD down
    fi

    # Pull latest images (if using registry)
    print_info "Pulling latest images..."
    $COMPOSE_CMD pull --ignore-pull-failures

    # Build and start containers
    print_info "Building and starting containers..."
    $COMPOSE_CMD up -d --build

    # Wait for application to be ready
    print_info "Waiting for application to start..."
    sleep 5

    # Check health status
    max_attempts=30
    attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if $COMPOSE_CMD ps | grep -q "matrica-app.*healthy\|matrica-app.*Up"; then
            break
        fi
        
        echo -ne "${YELLOW}⏳${NC} Waiting for application to be healthy... ($attempt/$max_attempts)\r"
        sleep 2
        ((attempt++))
    done
    echo ""

    # Final health check
    if $COMPOSE_CMD ps | grep -q "matrica-app.*healthy\|matrica-app.*Up"; then
        print_status "Application started successfully!"
    else
        print_error "Application failed to start properly"
        print_info "Checking logs..."
        $COMPOSE_CMD logs --tail=20 matrica
        exit 1
    fi
fi

echo ""
echo -e "${GREEN}🎉 Matrica Networks is now running!${NC}"
echo ""
echo -e "${PURPLE}📱 Access URLs:${NC}"
echo -e "  🌐 Website:        ${CYAN}http://localhost:8000${NC}"
echo -e "  👤 Employee Portal: ${CYAN}http://localhost:8000/portal/login.html${NC}"
echo -e "  🔧 Admin Dashboard: ${CYAN}http://localhost:8000/portal/admin.html${NC}"
echo ""
echo -e "${PURPLE}👨‍💼 Admin Credentials:${NC}"
echo -e "  Username: ${YELLOW}psychy${NC}"
echo -e "  Password: ${YELLOW}Ka05ml@2120${NC}"
echo ""
echo -e "${PURPLE}🛠 Management Commands:${NC}"
echo -e "  View logs:     ${CYAN}docker-compose logs -f matrica${NC}"
echo -e "  Stop server:   ${CYAN}./stop_server.sh${NC}"
echo -e "  Restart:       ${CYAN}docker-compose restart${NC}"
echo -e "  Shell access:  ${CYAN}docker-compose exec matrica sh${NC}"
echo ""
echo -e "${PURPLE}📊 Service Status:${NC}"
$COMPOSE_CMD ps

# Optional: Show real-time logs
echo ""
read -p "Do you want to view real-time logs? (y/N): " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${BLUE}📋 Showing real-time logs (Press Ctrl+C to exit):${NC}"
    echo ""
    $COMPOSE_CMD logs -f matrica
fi

echo ""
print_status "Startup script completed successfully!"
echo -e "${CYAN}Securing the digital frontier, one byte at a time.${NC}"