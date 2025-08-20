#!/bin/bash

# Matrica Networks - Stop Server Script
# 
# This script safely stops the Matrica Networks cybersecurity website
# with proper cleanup, backup options, and graceful shutdown.

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
echo -e "${RED}"
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
        NETWORKS - Shutdown Sequence
EOF
echo -e "${NC}"

echo -e "${RED}🛑 Stopping Matrica Networks Application...${NC}"
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
    print_error "Docker is not installed."
    exit 1
fi

if ! docker info &> /dev/null; then
    print_error "Docker is not running."
    exit 1
fi

# Check if Docker Compose is available
if ! command -v docker-compose &> /dev/null; then
    if ! docker compose version &> /dev/null; then
        print_error "Docker Compose is not available."
        exit 1
    fi
    COMPOSE_CMD="docker compose"
else
    COMPOSE_CMD="docker-compose"
fi

# Check if containers are running
if ! $COMPOSE_CMD ps -q | grep -q .; then
    print_warning "No containers are currently running."
    exit 0
fi

# Show current status
print_info "Current container status:"
$COMPOSE_CMD ps
echo ""

# Options for shutdown
echo -e "${PURPLE}🔧 Shutdown Options:${NC}"
echo "1. Graceful stop (recommended)"
echo "2. Quick stop"
echo "3. Stop and remove containers"
echo "4. Full cleanup (remove containers, volumes, and images)"
echo "5. Cancel"
echo ""

while true; do
    read -p "Select an option (1-5): " option
    case $option in
        1)
            shutdown_type="graceful"
            break
            ;;
        2)
            shutdown_type="quick"
            break
            ;;
        3)
            shutdown_type="remove"
            break
            ;;
        4)
            shutdown_type="cleanup"
            break
            ;;
        5)
            print_info "Shutdown cancelled."
            exit 0
            ;;
        *)
            print_warning "Invalid option. Please select 1-5."
            ;;
    esac
done

echo ""

# Backup option for important shutdowns
if [[ "$shutdown_type" == "remove" || "$shutdown_type" == "cleanup" ]]; then
    echo -e "${YELLOW}⚠ This operation will remove containers and may affect data.${NC}"
    read -p "Do you want to create a backup first? (Y/n): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Nn]$ ]]; then
        print_info "Creating backup before shutdown..."
        timestamp=$(date +%Y%m%d_%H%M%S)
        backup_dir="./backup_$timestamp"
        
        mkdir -p "$backup_dir"
        
        # Backup database if exists
        if [ -f "data/db/matrica.db" ]; then
            cp "data/db/matrica.db" "$backup_dir/"
            print_status "Database backed up to $backup_dir/matrica.db"
        fi
        
        # Backup storage files
        if [ -d "data/storage" ]; then
            tar -czf "$backup_dir/storage.tar.gz" -C data storage/
            print_status "Storage files backed up to $backup_dir/storage.tar.gz"
        fi
        
        # Backup logs
        if [ -d "data/logs" ]; then
            tar -czf "$backup_dir/logs.tar.gz" -C data logs/
            print_status "Logs backed up to $backup_dir/logs.tar.gz"
        fi
        
        print_status "Backup completed in $backup_dir"
        echo ""
    fi
fi

# Execute shutdown based on selected type
case $shutdown_type in
    "graceful")
        print_info "Performing graceful shutdown..."
        print_info "Sending SIGTERM to containers..."
        $COMPOSE_CMD stop --timeout 30
        print_status "All containers stopped gracefully"
        ;;
        
    "quick")
        print_info "Performing quick shutdown..."
        $COMPOSE_CMD stop --timeout 5
        print_status "All containers stopped quickly"
        ;;
        
    "remove")
        print_info "Stopping and removing containers..."
        $COMPOSE_CMD down --timeout 30
        print_status "Containers stopped and removed"
        
        print_info "Cleaning up unused networks..."
        docker network prune -f --filter label=com.docker.compose.project=$(basename $(pwd))
        print_status "Networks cleaned up"
        ;;
        
    "cleanup")
        print_warning "Performing full cleanup - this will remove ALL data!"
        read -p "Are you absolutely sure? Type 'YES' to continue: " confirm
        if [ "$confirm" != "YES" ]; then
            print_info "Full cleanup cancelled."
            exit 0
        fi
        
        print_info "Stopping and removing containers..."
        $COMPOSE_CMD down --timeout 30 -v --rmi local
        
        print_info "Removing volumes..."
        docker volume ls -q --filter label=com.docker.compose.project=$(basename $(pwd)) | xargs -r docker volume rm
        
        print_info "Cleaning up networks..."
        docker network prune -f --filter label=com.docker.compose.project=$(basename $(pwd))
        
        print_info "Removing local data directories..."
        rm -rf data/
        
        print_status "Full cleanup completed"
        ;;
esac

echo ""

# Show final status
remaining_containers=$(docker ps -a --filter label=com.docker.compose.project=$(basename $(pwd)) --format "table {{.Names}}\t{{.Status}}" | tail -n +2)

if [ -n "$remaining_containers" ]; then
    print_info "Remaining containers:"
    echo "$remaining_containers"
else
    print_status "No containers remaining"
fi

echo ""

# Show resource usage
if command -v docker &> /dev/null; then
    print_info "Current Docker resource usage:"
    echo "  Containers: $(docker ps -a | wc -l) total, $(docker ps | wc -l) running"
    echo "  Images: $(docker images | wc -l) total"
    echo "  Volumes: $(docker volume ls | wc -l) total"
    
    # Show disk space if available
    if df -h . &> /dev/null; then
        echo "  Disk space: $(df -h . | tail -1 | awk '{print $4}') available"
    fi
fi

echo ""

# Cleanup suggestions
case $shutdown_type in
    "graceful"|"quick")
        echo -e "${PURPLE}💡 Restart Options:${NC}"
        echo -e "  Start again:    ${CYAN}./start_server.sh${NC}"
        echo -e "  Start and view: ${CYAN}./start_server.sh && docker-compose logs -f${NC}"
        ;;
        
    "remove")
        echo -e "${PURPLE}💡 Next Steps:${NC}"
        echo -e "  Fresh start:    ${CYAN}./start_server.sh${NC}"
        echo -e "  View backups:   ${CYAN}ls -la backup_*/${NC}"
        echo -e "  Cleanup images: ${CYAN}docker image prune${NC}"
        ;;
        
    "cleanup")
        echo -e "${PURPLE}💡 Starting Fresh:${NC}"
        echo -e "  Initialize:     ${CYAN}./start_server.sh${NC}"
        echo -e "  System cleanup: ${CYAN}docker system prune -a${NC}"
        ;;
esac

echo ""

# Final message
print_status "Shutdown sequence completed successfully!"

case $shutdown_type in
    "graceful"|"quick")
        echo -e "${BLUE}Application stopped. Data preserved.${NC}"
        ;;
    "remove")
        echo -e "${YELLOW}Containers removed. Persistent data preserved.${NC}"
        ;;
    "cleanup")
        echo -e "${RED}Full cleanup completed. All data removed.${NC}"
        ;;
esac

echo -e "${CYAN}Thank you for using Matrica Networks.${NC}"