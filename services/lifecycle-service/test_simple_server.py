#!/usr/bin/env python3
"""
Test semplificato del server
"""
import asyncio
import aiohttp
import subprocess
import sys
import time
import os
import signal
from loguru import logger

async def test_simple_server():
    """Test semplificato"""
    
    logger.info("🚀 Test server semplificato...")
    
    # Avvia il server in background
    process = subprocess.Popen([
        sys.executable, "main.py", "server"
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    try:
        # Aspetta 5 secondi
        await asyncio.sleep(5)
        
        # Test health check
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get("http://localhost:8001/health", timeout=aiohttp.ClientTimeout(total=5)) as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.info(f"✅ Server risponde: {data.get('status', 'unknown')}")
                        return True
                    else:
                        logger.error(f"❌ Server risposta status: {response.status}")
                        return False
            except Exception as e:
                logger.error(f"❌ Errore connessione: {e}")
                return False
                
    finally:
        # Kill process
        try:
            process.terminate()
            process.wait(timeout=3)
        except:
            process.kill()

if __name__ == "__main__":
    success = asyncio.run(test_simple_server())
    sys.exit(0 if success else 1)
