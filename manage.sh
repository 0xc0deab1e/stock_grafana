#!/bin/bash

# Configuration
NGINX_PORT=${NGINX_PORT:-8081}
GRAFANA_PORT=${GRAFANA_PORT:-3001}
VSCODE_PORT=${VSCODE_PORT:-8443}
INFLUXDB_PORT=${INFLUXDB_PORT:-8086}

# OS Detection and Data Path
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" || "$OSTYPE" == "win32" ]]; then
    DEFAULT_DATA_PATH="C:/docker_storage/stock_crawler"
else
    DEFAULT_DATA_PATH="/data/jh"
fi

function generate_token() {
    length=$1
    openssl rand -hex "$length" 2>/dev/null || LC_ALL=C tr -dc 'a-f0-9' < /dev/urandom | head -c "$((length * 2))"
}

function init() {
    echo "Initializing environment..."
    
    # Use existing DATA_PATH from .env if it exists, else use default
    if [ -f .env ]; then
        source .env 2>/dev/null
    fi
    DATA_PATH=${DATA_PATH:-$DEFAULT_DATA_PATH}

    mkdir -p "$DATA_PATH/influxdb" "$DATA_PATH/grafana" "$DATA_PATH/vscode"

    # Nginx Configuration
    NGINX_CONF_DIR="infra-nginx/conf"
    NGINX_CONF_FILE="$NGINX_CONF_DIR/nginx.conf"
    mkdir -p "$NGINX_CONF_DIR"
    
    if [ -d "$NGINX_CONF_FILE" ]; then
        echo "Fixing Docker error: Removing directory $NGINX_CONF_FILE..."
        rm -rf "$NGINX_CONF_FILE"
    fi

    if [ ! -f "$NGINX_CONF_FILE" ]; then
        cat <<'EOF' > "$NGINX_CONF_FILE"
events {}
http {
    upstream influx { server influxdb:8086; }
    upstream grafana { server grafana:3000; }
    upstream vscode { server vscode:8443; }
    server {
        listen 80;
        location /influx/ { 
            proxy_pass http://influx/; 
            proxy_set_header Host $host;
        }
        location /grafana/ { 
            proxy_pass http://grafana/; 
            proxy_set_header Host $host;
        }
        location / {
            proxy_pass http://vscode/;
            proxy_set_header Host $host;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
        }
    }
}
EOF
        echo "Nginx configuration generated."
    fi

    if [ ! -f .env ]; then
        INFLUXDB_TOKEN=$(generate_token 32)
        VSCODE_PASSWORD=$(generate_token 6) # 12 chars hex
        
        cat <<EOF > .env
DATA_PATH=$DATA_PATH
NGINX_PORT=$NGINX_PORT
GRAFANA_PORT=$GRAFANA_PORT
VSCODE_PORT=$VSCODE_PORT
INFLUXDB_PORT=$INFLUXDB_PORT
INFLUXDB_TOKEN=$INFLUXDB_TOKEN
VSCODE_PASSWORD=$VSCODE_PASSWORD
INFLUXDB_ORG=my-org
INFLUXDB_BUCKET=stock_data
EOF
        echo ".env file generated."
    else
        echo ".env already exists. Skipping generation."
    fi
}

function up() {
    echo "Starting services..."
    docker compose up -d "$@"
    
    # Load ports for display
    if [ -f .env ]; then source .env; fi
    
    echo ""
    echo "Services are available at:"
    echo "------------------------------------------------"
    echo "Nginx (Gateway) : http://localhost:${NGINX_PORT:-8081}"
    echo "VS Code         : http://localhost:${VSCODE_PORT:-8443}"
    echo "Grafana         : http://localhost:${GRAFANA_PORT:-3001}"
    echo "InfluxDB        : http://localhost:${INFLUXDB_PORT:-8086}"
    echo "------------------------------------------------"
}

function clean() {
    echo "Cleaning up..."
    docker compose down -v
    rm -f .env
    echo "Note: $DATA_PATH was NOT deleted for safety."
}

# Command dispatcher
case "$1" in
    init)
        init
        ;;
    up)
        shift
        up "$@"
        ;;
    clean)
        clean
        ;;
    *)
        echo "Usage: $0 {init|up|clean}"
        exit 1
        ;;
esac
