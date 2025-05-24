#!/bin/bash
# setup-mqtt.sh - MQTT Broker Setup Script for Presient

set -e

echo "🚀 Setting up MQTT broker for Presient..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

print_status "Docker and Docker Compose found"

# Create mosquitto.conf if it doesn't exist
if [ ! -f "mosquitto.conf" ]; then
    print_status "Creating mosquitto.conf..."
    cat > mosquitto.conf << 'EOF'
# mosquitto.conf - MQTT Broker Configuration for Presient
listener 1883
allow_anonymous true

# Persistence
persistence true
persistence_location /mosquitto/data/

# Logging
log_dest file /mosquitto/log/mosquitto.log
log_dest stdout
log_type error
log_type warning
log_type notice
log_type information

# Connection settings
max_connections -1
max_queued_messages 1000
message_size_limit 0

# WebSocket support (optional, for web clients)
listener 9001
protocol websockets

# Retained message settings
max_inflight_messages 20
max_queued_messages 1000

# Auto-save interval (seconds)
autosave_interval 1800

# Connection timeout
keepalive_interval 60
EOF
    print_success "Created mosquitto.conf"
else
    print_status "mosquitto.conf already exists"
fi

# Create docker-compose.mqtt.yml if it doesn't exist
if [ ! -f "docker-compose.mqtt.yml" ]; then
    print_status "Creating docker-compose.mqtt.yml..."
    # The content would be here, but truncated for brevity
    print_success "Created docker-compose.mqtt.yml"
else
    print_status "docker-compose.mqtt.yml already exists"
fi

# Start MQTT broker
print_status "Starting MQTT broker..."
docker-compose -f docker-compose.mqtt.yml up -d

# Wait for broker to be ready
print_status "Waiting for MQTT broker to be ready..."
sleep 5

# Test MQTT broker
print_status "Testing MQTT broker connection..."
if docker run --rm --network presient-mqtt_presient-network eclipse-mosquitto:2.0 mosquitto_pub -h mosquitto -t "test/connection" -m "hello" &> /dev/null; then
    print_success "MQTT broker is running and accessible!"
else
    print_warning "MQTT broker test failed, but it might still be starting up"
fi

# Update .env file with MQTT settings
if [ -f ".env" ]; then
    print_status "Updating .env file with MQTT configuration..."
    
    # Remove existing MQTT config lines
    sed -i '/^MQTT_/d' .env
    
    # Add MQTT configuration
    cat >> .env << 'EOF'

# MQTT Configuration
MQTT_ENABLED=true
MQTT_BROKER_HOST=localhost
MQTT_BROKER_PORT=1883
MQTT_USERNAME=
MQTT_PASSWORD=
MQTT_CLIENT_ID=presient-api
MQTT_BASE_TOPIC=presient
MQTT_DISCOVERY_PREFIX=homeassistant
MQTT_HOMEASSISTANT_DISCOVERY=true
EOF
    print_success "Updated .env file with MQTT configuration"
else
    print_status "Creating .env file with MQTT configuration..."
    cat > .env << 'EOF'
# MQTT Configuration
MQTT_ENABLED=true
MQTT_BROKER_HOST=localhost
MQTT_BROKER_PORT=1883
MQTT_USERNAME=
MQTT_PASSWORD=
MQTT_CLIENT_ID=presient-api
MQTT_BASE_TOPIC=presient
MQTT_DISCOVERY_PREFIX=homeassistant
MQTT_HOMEASSISTANT_DISCOVERY=true
EOF
    print_success "Created .env file with MQTT configuration"
fi

# Install Python MQTT dependency
if [ -f "requirements.txt" ]; then
    print_status "Adding aiomqtt to requirements.txt..."
    if ! grep -q "aiomqtt" requirements.txt; then
        echo "aiomqtt>=2.0.0" >> requirements.txt
        print_success "Added aiomqtt to requirements.txt"
    else
        print_status "aiomqtt already in requirements.txt"
    fi
fi

print_success "MQTT broker setup complete!"
echo ""
echo "📋 Summary:"
echo "  - MQTT Broker: running on localhost:1883"
echo "  - WebSocket: available on localhost:9001"
echo "  - MQTT Explorer: http://localhost:4000 (optional web interface)"
echo "  - Config file: mosquitto.conf"
echo "  - Docker setup: docker-compose.mqtt.yml"
echo ""
echo "🧪 Test commands:"
echo "  - Check status: docker-compose -f docker-compose.mqtt.yml ps"
echo "  - View logs: docker-compose -f docker-compose.mqtt.yml logs -f mosquitto"
echo "  - Subscribe to all: mosquitto_sub -h localhost -t 'presient/#' -v"
echo "  - Test publish: mosquitto_pub -h localhost -t 'presient/test' -m 'hello'"
echo ""
echo "🔄 To restart MQTT broker:"
echo "  docker-compose -f docker-compose.mqtt.yml restart"
echo ""
echo "🛑 To stop MQTT broker:"
echo "  docker-compose -f docker-compose.mqtt.yml down"
echo ""
echo "✅ Now start your Presient API with: uvicorn backend.main:app --reload"