#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Stopping services...${NC}"

# Function to check if process exists
process_exists() {
    pgrep -f "$1" > /dev/null
}

# Stop processes on 127.0.0.1:5003
echo -n "Stopping processes on 127.0.0.1:5003... "
if process_exists "127.0.0.1:5003"; then
    if pkill -f -9 127.0.0.1:5003; then
        echo -e "${GREEN}SUCCESS${NC}"
        echo -e "${GREEN}✓ Processes on 127.0.0.1:5003 killed${NC}"
    else
        echo -e "${RED}FAILED${NC}"
        echo -e "${RED}✗ Failed to kill processes on 127.0.0.1:5003${NC}"
    fi
else
    echo -e "${YELLOW}NOT RUNNING${NC}"
    echo -e "${YELLOW}✓ No processes found on 127.0.0.1:5003${NC}"
fi

# Stop python3 run_worker.py
echo -n "Stopping python3 run_worker.py... "
if process_exists "python3 run_worker.py"; then
    if pkill -f "python3 run_worker.py"; then
        echo -e "${GREEN}SUCCESS${NC}"
        echo -e "${GREEN}✓ python3 run_worker.py killed${NC}"
    else
        echo -e "${RED}FAILED${NC}"
        echo -e "${RED}✗ Failed to kill python3 run_worker.py${NC}"
    fi
else
    echo -e "${YELLOW}NOT RUNNING${NC}"
    echo -e "${YELLOW}✓ python3 run_worker.py was not running${NC}"
fi

echo -e "${GREEN}Kill script completed!${NC}"

