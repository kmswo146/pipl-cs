#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Starting services...${NC}"

# Start Gunicorn server
echo -n "Starting Gunicorn server... "
if gunicorn -w 4 -b 127.0.0.1:5003 app:app --daemon; then
    echo -e "${GREEN}SUCCESS${NC}"
    
    # Check if the process is actually running
    sleep 2
    if pgrep -f "gunicorn.*app:app" > /dev/null; then
        echo -e "${GREEN}✓ Gunicorn server is running on 127.0.0.1:5003${NC}"
    else
        echo -e "${RED}✗ Gunicorn server failed to start properly${NC}"
        exit 1
    fi
else
    echo -e "${RED}FAILED${NC}"
    echo -e "${RED}✗ Failed to start Gunicorn server${NC}"
    exit 1
fi

# Start worker process
echo -n "Starting worker process... "
if nohup python3 run_worker.py > worker.log 2>&1 & then
    WORKER_PID=$!
    echo -e "${GREEN}SUCCESS${NC}"
    
    # Wait a moment and check if the worker is still running
    sleep 2
    if kill -0 $WORKER_PID 2>/dev/null; then
        echo -e "${GREEN}✓ Worker process is running (PID: $WORKER_PID)${NC}"
        echo -e "${YELLOW}Worker logs are being written to worker.log${NC}"
    else
        echo -e "${RED}✗ Worker process failed to start or crashed immediately${NC}"
        echo -e "${YELLOW}Check worker.log for error details${NC}"
        exit 1
    fi
else
    echo -e "${RED}FAILED${NC}"
    echo -e "${RED}✗ Failed to start worker process${NC}"
    exit 1
fi

echo -e "${GREEN}All services started successfully!${NC}"

