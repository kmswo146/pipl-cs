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

# Stop Gunicorn server
echo -n "Stopping Gunicorn server... "
if process_exists "gunicorn.*app:app"; then
    if pkill -f "gunicorn.*app:app"; then
        # Wait a moment and check if it's really stopped
        sleep 2
        if ! process_exists "gunicorn.*app:app"; then
            echo -e "${GREEN}SUCCESS${NC}"
            echo -e "${GREEN}✓ Gunicorn server stopped${NC}"
        else
            echo -e "${YELLOW}FORCE KILLING${NC}"
            pkill -9 -f "gunicorn.*app:app"
            sleep 1
            if ! process_exists "gunicorn.*app:app"; then
                echo -e "${GREEN}✓ Gunicorn server force stopped${NC}"
            else
                echo -e "${RED}✗ Failed to stop Gunicorn server${NC}"
            fi
        fi
    else
        echo -e "${RED}FAILED${NC}"
        echo -e "${RED}✗ Failed to send stop signal to Gunicorn${NC}"
    fi
else
    echo -e "${YELLOW}NOT RUNNING${NC}"
    echo -e "${YELLOW}✓ Gunicorn server was not running${NC}"
fi

# Stop worker process
echo -n "Stopping worker process... "
if process_exists "python3 run_worker.py"; then
    if pkill -f "python3 run_worker.py"; then
        # Wait a moment and check if it's really stopped
        sleep 2
        if ! process_exists "python3 run_worker.py"; then
            echo -e "${GREEN}SUCCESS${NC}"
            echo -e "${GREEN}✓ Worker process stopped${NC}"
        else
            echo -e "${YELLOW}FORCE KILLING${NC}"
            pkill -9 -f "python3 run_worker.py"
            sleep 1
            if ! process_exists "python3 run_worker.py"; then
                echo -e "${GREEN}✓ Worker process force stopped${NC}"
            else
                echo -e "${RED}✗ Failed to stop worker process${NC}"
            fi
        fi
    else
        echo -e "${RED}FAILED${NC}"
        echo -e "${RED}✗ Failed to send stop signal to worker${NC}"
    fi
else
    echo -e "${YELLOW}NOT RUNNING${NC}"
    echo -e "${YELLOW}✓ Worker process was not running${NC}"
fi

# Final status check
echo ""
if ! process_exists "gunicorn.*app:app" && ! process_exists "python3 run_worker.py"; then
    echo -e "${GREEN}All services stopped successfully!${NC}"
else
    echo -e "${RED}Some processes may still be running. Check manually with:${NC}"
    echo -e "${YELLOW}  ps aux | grep -E '(gunicorn|run_worker)'${NC}"
fi

