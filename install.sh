#!/usr/bin/env bash
#
# MemU MCP Server - Automated Installation Script
# This script automates the Docker-based installation of MemU MCP Server
#

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
IMAGE_NAME="memu-mcp-server"
CONTAINER_NAME="memu-mcp"
DATA_DIR="${HOME}/.memu/data"
CONFIG_DIR="${HOME}/.memu"

# Helper functions
info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

# Check if Docker is installed
check_docker() {
    info "Checking Docker installation..."
    if ! command -v docker &> /dev/null; then
        error "Docker is not installed. Please install Docker first: https://docs.docker.com/get-docker/"
    fi
    
    if ! docker info &> /dev/null; then
        error "Docker is not running. Please start Docker and try again."
    fi
    
    success "Docker is installed and running"
}

# Create necessary directories
create_directories() {
    info "Creating directories..."
    mkdir -p "$DATA_DIR"
    mkdir -p "$CONFIG_DIR"
    success "Directories created at $CONFIG_DIR"
}

# Create .env file if it doesn't exist
create_env_file() {
    local env_file="$CONFIG_DIR/.env"
    
    if [ -f "$env_file" ]; then
        warning ".env file already exists at $env_file"
        read -p "Do you want to overwrite it? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            info "Keeping existing .env file"
            return
        fi
    fi
    
    info "Creating .env file..."
    
    # Ask user for provider
    echo ""
    echo "Select your LLM provider:"
    echo "1) Ollama (Local)"
    echo "2) LMStudio (Local)"
    echo "3) OpenRouter"
    echo "4) DeepInfra"
    echo "5) Fireworks AI"
    echo "6) OpenAI"
    echo "7) Custom"
    read -p "Enter choice (1-7): " provider_choice
    
    case $provider_choice in
        1)
            PROVIDER="ollama"
            BASE_URL="http://host.docker.internal:11434/v1"
            read -p "Enter Ollama model name [llama3]: " MODEL
            MODEL=${MODEL:-llama3}
            API_KEY="ollama"
            ;;
        2)
            PROVIDER="lmstudio"
            BASE_URL="http://host.docker.internal:1234/v1"
            read -p "Enter LMStudio model name [local-model]: " MODEL
            MODEL=${MODEL:-local-model}
            API_KEY="lm-studio"
            ;;
        3)
            PROVIDER="openrouter"
            BASE_URL="https://openrouter.ai/api/v1"
            read -p "Enter OpenRouter API key: " API_KEY
            read -p "Enter model name [anthropic/claude-3.5-sonnet]: " MODEL
            MODEL=${MODEL:-anthropic/claude-3.5-sonnet}
            ;;
        4)
            PROVIDER="deepinfra"
            BASE_URL="https://api.deepinfra.com/v1/openai"
            read -p "Enter DeepInfra API key: " API_KEY
            read -p "Enter model name [meta-llama/Meta-Llama-3.1-70B-Instruct]: " MODEL
            MODEL=${MODEL:-meta-llama/Meta-Llama-3.1-70B-Instruct}
            ;;
        5)
            PROVIDER="fireworks"
            BASE_URL="https://api.fireworks.ai/inference/v1"
            read -p "Enter Fireworks AI API key: " API_KEY
            read -p "Enter model name [accounts/fireworks/models/llama-v3p1-70b-instruct]: " MODEL
            MODEL=${MODEL:-accounts/fireworks/models/llama-v3p1-70b-instruct}
            ;;
        6)
            PROVIDER="openai"
            BASE_URL="https://api.openai.com/v1"
            read -p "Enter OpenAI API key: " API_KEY
            read -p "Enter chat model [gpt-4o-mini]: " MODEL
            MODEL=${MODEL:-gpt-4o-mini}
            ;;
        7)
            PROVIDER="custom"
            read -p "Enter base URL: " BASE_URL
            read -p "Enter API key: " API_KEY
            read -p "Enter model name: " MODEL
            ;;
        *)
            error "Invalid choice"
            ;;
    esac
    
    # Create .env file
    cat > "$env_file" <<EOF
# MemU MCP Server Configuration
MEMU_PROVIDER=$PROVIDER

# LLM Configuration
LLM_BASE_URL=$BASE_URL
LLM_API_KEY=$API_KEY
LLM_CHAT_MODEL=$MODEL
LLM_EMBED_MODEL=$MODEL

# Database Configuration
DB_PROVIDER=inmemory

# Retrieval Configuration
RETRIEVE_METHOD=rag
EOF
    
    success ".env file created at $env_file"
}

# Build Docker image
build_image() {
    info "Building Docker image..."
    
    if ! docker build -t "$IMAGE_NAME" .; then
        error "Failed to build Docker image"
    fi
    
    success "Docker image built successfully"
}

# Detect OS and set network mode
detect_network_mode() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        echo "--network=host"
    else
        echo ""  # Docker for Mac/Windows uses host.docker.internal
    fi
}

# Run container
run_container() {
    info "Running container..."
    
    # Stop existing container if running
    if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
        warning "Stopping existing container..."
        docker stop "$CONTAINER_NAME" 2>/dev/null || true
        docker rm "$CONTAINER_NAME" 2>/dev/null || true
    fi
    
    local network_mode=$(detect_network_mode)
    
    docker run -d \
        --name "$CONTAINER_NAME" \
        --env-file "$CONFIG_DIR/.env" \
        -v "$DATA_DIR:/data" \
        $network_mode \
        "$IMAGE_NAME"
    
    success "Container is running as $CONTAINER_NAME"
}

# Show usage information
show_usage() {
    echo ""
    echo "=========================================="
    echo "MemU MCP Server Installation Complete!"
    echo "=========================================="
    echo ""
    echo "Configuration files:"
    echo "  - Config directory: $CONFIG_DIR"
    echo "  - Data directory: $DATA_DIR"
    echo "  - Environment file: $CONFIG_DIR/.env"
    echo ""
    echo "Docker container:"
    echo "  - Image: $IMAGE_NAME"
    echo "  - Container: $CONTAINER_NAME"
    echo ""
    echo "Useful commands:"
    echo "  - View logs:        docker logs -f $CONTAINER_NAME"
    echo "  - Stop server:      docker stop $CONTAINER_NAME"
    echo "  - Start server:     docker start $CONTAINER_NAME"
    echo "  - Restart server:   docker restart $CONTAINER_NAME"
    echo "  - Remove container: docker rm -f $CONTAINER_NAME"
    echo ""
    echo "To use with Claude Desktop or other MCP clients,"
    echo "configure them to use stdio transport with this command:"
    echo "  docker run -i --rm --env-file $CONFIG_DIR/.env -v $DATA_DIR:/data $IMAGE_NAME"
    echo ""
}

# Main installation flow
main() {
    echo ""
    echo "=========================================="
    echo "MemU MCP Server - Automated Installer"
    echo "=========================================="
    echo ""
    
    check_docker
    create_directories
    create_env_file
    build_image
    
    # Ask if user wants to run the container now
    echo ""
    read -p "Do you want to run the container now? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        run_container
    else
        info "Skipping container run. You can run it later with:"
        echo "  docker run -d --name $CONTAINER_NAME --env-file $CONFIG_DIR/.env -v $DATA_DIR:/data $IMAGE_NAME"
    fi
    
    show_usage
    success "Installation complete!"
}

# Run main installation
main "$@"
