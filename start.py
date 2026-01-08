#!/usr/bin/env python3
"""Sonia Launcher"""

import sys
import subprocess
import time
from pathlib import Path
from logger_config import logger
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def main():
    logger.info("Launching Sonia System...")
    
    # 1. Launch Server (Brain)
    logger.info("Starting Brain (Server)...")
    server_cmd = [sys.executable, "server/main.py"]
    server_process = subprocess.Popen(server_cmd)
    
    # Wait for server to be ready (naive wait)
    time.sleep(3)
    
    # 2. Launch Client (Body)
    logger.info("Starting Body (Client)...")
    client_cmd = [sys.executable, "client/main.py"]
    client_process = subprocess.Popen(client_cmd)
    
    try:
        # Keep main script alive watching processes
        while True:
            if server_process.poll() is not None:
                logger.error("Server died!")
                client_process.terminate()
                break
            if client_process.poll() is not None:
                logger.info("Client closed. Shutting down server...")
                server_process.terminate()
                break
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        server_process.terminate()
        client_process.terminate()
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        try:
            server_process.terminate()
            client_process.terminate()
        except:
             pass

if __name__ == "__main__":
    main()