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
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} [CRON] $1"
}

log_error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] [CRON] ERROR:${NC} $1"
}

log_success() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] [CRON] SUCCESS:${NC} $1"
}

# Function to run the pipeline
run_pipeline() {
    local categories=${PIPELINE_CATEGORIES:-"Baseball,Hockey,Basketball,Football"}
    local concurrency=${PIPELINE_MAX_CONCURRENCY:-3}
    local delay=${PIPELINE_DELAY:-1.0}
    
    log "Starting scheduled pipeline execution..."
    log "  Categories: $categories"
    log "  Concurrency: $concurrency"
    log "  Delay: ${delay}s"
    
    # Convert comma-separated categories to space-separated for CLI
    local categories_array=$(echo "$categories" | tr ',' ' ')
    
    # Set PYTHONPATH
    export PYTHONPATH="/app/src:$PYTHONPATH"
    
    # Run the pipeline
    if python -m scraper.pipeline --categories $categories_array --concurrency "$concurrency" --delay "$delay"; then
        log_success "Scheduled pipeline execution completed successfully"
        return 0
    else
        log_error "Scheduled pipeline execution failed"
        return 1
    fi
}

# Main execution
main() {
    log "=== Scheduled Pipeline Execution Starting ==="
    
    # Check if we're in the right directory
    if [[ ! -f "src/scraper/pipeline.py" ]]; then
        log_error "Pipeline script not found. Current directory: $(pwd)"
        log_error "Contents of current directory:"
        ls -la
        exit 1
    fi
    
    # Run the pipeline
    if run_pipeline; then
        log_success "Scheduled pipeline execution completed"
        exit 0
    else
        log_error "Scheduled pipeline execution failed"
        exit 1
    fi
}

# Handle signals gracefully
trap 'log "Received signal, shutting down gracefully..."; exit 0' SIGTERM SIGINT

# Run main function
main "$@"
