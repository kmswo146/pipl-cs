#!/usr/bin/env python3
"""
Run the worker process from the main directory
"""
import sys
import os

# Add worker directory to path
worker_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'worker')
sys.path.append(worker_dir)

# Import and run the worker
from worker import worker_loop

if __name__ == "__main__":
    worker_loop() 