#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] SUCCESS:${NC} $1"
}

log_error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1"
}

# Check if we're in the right directory
if [[ ! -f "src/models.py" ]]; then
    log_error "Please run this script from the project root directory"
    exit 1
fi

log "Starting TAG Grading Scraper Reporting Website..."

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    log_error "Python 3 is required but not installed"
    exit 1
fi

# Check if Node.js is available
if ! command -v node &> /dev/null; then
    log_error "Node.js is required but not installed"
    exit 1
fi

# Check if npm is available
if ! command -v npm &> /dev/null; then
    log_error "npm is required but not installed"
    exit 1
fi

log "Installing backend dependencies..."
cd backend
if [[ ! -d "venv" ]]; then
    log "Creating Python virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate
pip install -r requirements.txt
log_success "Backend dependencies installed"

log "Installing frontend dependencies..."
cd ../frontend
if [[ ! -d "node_modules" ]]; then
    log "Installing npm packages..."
    npm install
fi
log_success "Frontend dependencies installed"

log "Starting backend API server..."
cd ../backend
source venv/bin/activate
python main.py &
BACKEND_PID=$!

# Wait for backend to start
log "Waiting for backend to start..."
sleep 5

# Check if backend is running
if ! curl -s http://localhost:8000/api/health > /dev/null; then
    log_error "Backend failed to start"
    kill $BACKEND_PID 2>/dev/null || true
    exit 1
fi

log_success "Backend API server started on http://localhost:8000"

log "Starting frontend development server..."
cd ../frontend
npm start &
FRONTEND_PID=$!

# Wait for frontend to start
log "Waiting for frontend to start..."
sleep 10

log_success "Frontend development server started on http://localhost:3000"

log_success "Reporting website is now running!"
echo ""
echo "🌐 Frontend: http://localhost:3000"
echo "🔧 Backend API: http://localhost:8000"
echo "📚 API Documentation: http://localhost:8000/api/docs"
echo ""
echo "Press Ctrl+C to stop both servers"

# Function to cleanup on exit
cleanup() {
    log "Stopping servers..."
    kill $BACKEND_PID 2>/dev/null || true
    kill $FRONTEND_PID 2>/dev/null || true
    log_success "Servers stopped"
    exit 0
}

# Set trap to cleanup on exit
trap cleanup SIGINT SIGTERM

# Wait for user to stop
wait
