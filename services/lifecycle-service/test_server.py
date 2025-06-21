#!/usr/bin/env python3
"""
Test per verificare che il server si avvii correttamente
"""
import asyncio
import aiohttp
import sys
import subprocess
import time
import signal
import os
from loguru import logger

async def test_server_startup():
    """Test di avvio del server"""
    
    logger.info("🚀 Test avvio server...")
    
    # Avvia il server in un processo separato
    process = subprocess.Popen([
        sys.executable, "main.py", "server"
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
       preexec_fn=os.setsid)
    
    try:
        # Aspetta che il server si avvii
        await asyncio.sleep(3)
        
        # Test delle API endpoints
        async with aiohttp.ClientSession() as session:
            
            # Test health check
            try:
                async with session.get("http://localhost:8001/health") as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.info(f"✅ Health check OK: {data}")
                    else:
                        logger.error(f"❌ Health check failed: {response.status}")
                        return False
            except Exception as e:
                logger.error(f"❌ Errore connessione health: {e}")
                return False
            
            # Test stats endpoint
            try:
                async with session.get("http://localhost:8001/stats") as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.info(f"✅ Stats OK: {data.get('summary', {}).get('total_series', 0)} serie")
                    else:
                        logger.error(f"❌ Stats failed: {response.status}")
                        return False
            except Exception as e:
                logger.error(f"❌ Errore connessione stats: {e}")
                return False
            
            # Test config endpoint
            try:
                async with session.get("http://localhost:8001/config") as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.info(f"✅ Config OK: {len(data.get('rules', {}))} regole")
                    else:
                        logger.error(f"❌ Config failed: {response.status}")
                        return False
            except Exception as e:
                logger.error(f"❌ Errore connessione config: {e}")
                return False
                
        logger.info("🎉 Tutti i test API passati!")
        return True
        
    finally:
        # Termina il processo del server
        try:
            os.killpg(os.getpgid(process.pid), signal.SIGTERM)
            process.wait(timeout=5)
        except:
            try:
                os.killpg(os.getpgid(process.pid), signal.SIGKILL)
            except:
                pass

if __name__ == "__main__":
    success = asyncio.run(test_server_startup())
    if success:
        logger.info("🎉 Test server completato con successo!")
        sys.exit(0)
    else:
        logger.error("❌ Test server fallito!")
        sys.exit(1)
