#!/bin/bash

# Daily Journal API Deployment Script
# Usage: ./deploy.sh [start|stop|restart|status|logs]

set -e

# Configuration
APP_NAME="daily-journal-api"
PORT=8000
WORKERS=4
PID_FILE="/tmp/${APP_NAME}.pid"
LOG_FILE="/tmp/${APP_NAME}.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_requirements() {
    log_info "Checking requirements..."
    
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 is not installed"
        exit 1
    fi
    
    if [ ! -f "requirements.txt" ]; then
        log_error "requirements.txt not found"
        exit 1
    fi
    
    if [ ! -f ".env" ]; then
        log_warning ".env file not found, copying from .env.example"
        if [ -f ".env.example" ]; then
            cp .env.example .env
            log_info "Please edit .env file with your configuration"
        else
            log_error ".env.example not found"
            exit 1
        fi
    fi
    
    log_success "Requirements check passed"
}

install_dependencies() {
    log_info "Installing dependencies..."
    
    if [ ! -d "venv" ]; then
        log_info "Creating virtual environment..."
        python3 -m venv venv
    fi
    
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    
    # Install gunicorn for production
    pip install gunicorn
    
    log_success "Dependencies installed"
}

start_server() {
    if [ -f "$PID_FILE" ] && kill -0 $(cat "$PID_FILE") 2>/dev/null; then
        log_warning "Server is already running (PID: $(cat $PID_FILE))"
        return 1
    fi
    
    log_info "Starting Daily Journal API..."
    check_requirements
    install_dependencies
    
    source venv/bin/activate
    
    # Create data directory
    mkdir -p data
    
    # Start server
    if [ "${ENVIRONMENT:-development}" = "production" ]; then
        log_info "Starting in production mode with gunicorn..."
        gunicorn src.api.main:app \
            -w $WORKERS \
            -k uvicorn.workers.UvicornWorker \
            --bind 0.0.0.0:$PORT \
            --daemon \
            --pid $PID_FILE \
            --access-logfile $LOG_FILE \
            --error-logfile $LOG_FILE
    else
        log_info "Starting in development mode..."
        nohup python run.py > $LOG_FILE 2>&1 &
        echo $! > $PID_FILE
    fi
    
    sleep 2
    
    if [ -f "$PID_FILE" ] && kill -0 $(cat "$PID_FILE") 2>/dev/null; then
        log_success "Server started successfully (PID: $(cat $PID_FILE))"
        log_info "Server running on http://localhost:$PORT"
        log_info "API Documentation: http://localhost:$PORT/docs"
    else
        log_error "Failed to start server"
        exit 1
    fi
}

stop_server() {
    if [ ! -f "$PID_FILE" ]; then
        log_warning "PID file not found, server may not be running"
        return 1
    fi
    
    PID=$(cat "$PID_FILE")
    
    if kill -0 $PID 2>/dev/null; then
        log_info "Stopping server (PID: $PID)..."
        kill $PID
        
        # Wait for graceful shutdown
        for i in {1..10}; do
            if ! kill -0 $PID 2>/dev/null; then
                break
            fi
            sleep 1
        done
        
        # Force kill if still running
        if kill -0 $PID 2>/dev/null; then
            log_warning "Forcing server shutdown..."
            kill -9 $PID
        fi
        
        rm -f "$PID_FILE"
        log_success "Server stopped"
    else
        log_warning "Server not running"
        rm -f "$PID_FILE"
    fi
}

restart_server() {
    log_info "Restarting server..."
    stop_server
    sleep 2
    start_server
}

server_status() {
    if [ -f "$PID_FILE" ] && kill -0 $(cat "$PID_FILE") 2>/dev/null; then
        PID=$(cat "$PID_FILE")
        log_success "Server is running (PID: $PID)"
        
        # Check if port is listening
        if netstat -tuln | grep ":$PORT " > /dev/null; then
            log_info "Port $PORT is listening"
        else
            log_warning "Port $PORT is not listening"
        fi
        
        # Test health endpoint
        if command -v curl &> /dev/null; then
            if curl -f -s "http://localhost:$PORT/" > /dev/null; then
                log_success "Health check passed"
            else
                log_error "Health check failed"
            fi
        fi
    else
        log_error "Server is not running"
        if [ -f "$PID_FILE" ]; then
            rm -f "$PID_FILE"
        fi
    fi
}

show_logs() {
    if [ -f "$LOG_FILE" ]; then
        log_info "Showing server logs (last 50 lines):"
        echo "----------------------------------------"
        tail -n 50 "$LOG_FILE"
    else
        log_warning "Log file not found"
    fi
}

run_tests() {
    log_info "Running API tests..."
    source venv/bin/activate
    
    # Check if server is running
    if ! curl -f -s "http://localhost:$PORT/" > /dev/null; then
        log_error "Server is not running. Start the server first with: ./deploy.sh start"
        exit 1
    fi
    
    python test_api.py
}

# Main script
case "${1:-help}" in
    start)
        start_server
        ;;
    stop)
        stop_server
        ;;
    restart)
        restart_server
        ;;
    status)
        server_status
        ;;
    logs)
        show_logs
        ;;
    test)
        run_tests
        ;;
    help|*)
        echo "Daily Journal API Deployment Script"
        echo ""
        echo "Usage: $0 {start|stop|restart|status|logs|test|help}"
        echo ""
        echo "Commands:"
        echo "  start    - Start the API server"
        echo "  stop     - Stop the API server"
        echo "  restart  - Restart the API server"
        echo "  status   - Check server status"
        echo "  logs     - Show server logs"
        echo "  test     - Run API tests"
        echo "  help     - Show this help message"
        echo ""
        echo "Environment Variables:"
        echo "  ENVIRONMENT  - Set to 'production' for production mode"
        echo "  PORT         - Server port (default: 8000)"
        echo ""
        echo "Examples:"
        echo "  $0 start                    # Start in development mode"
        echo "  ENVIRONMENT=production $0 start  # Start in production mode"
        echo "  PORT=3001 $0 start         # Start on port 3001"
        ;;
esac
