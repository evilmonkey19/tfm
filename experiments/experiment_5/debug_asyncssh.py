import asyncio
import asyncssh
import sys
import logging
 
logging.basicConfig(level = logging.INFO)
logger = logging.getLogger()
 
bufferSize = 4096
 
async def run_client() -> None:
    logger.info("Connecting to server...")
    async with asyncssh.connect('localhost', username='sampol', password='sampol', port=2222) as conn:
        logger.info("Successful connection! Waiting for intial banner...")
 
        async with conn.create_process(term_type="xterm") as proc:
            logger.info("Waiting for initial data...")
            welcomeMessage = await proc.stdout.read(bufferSize)
            logger.info(welcomeMessage)
 
            logger.info("Writing command...")
            proc.stdin.write("test\r\n")
            response = await proc.stdout.read(bufferSize)
            logger.info(response)
 
try:
    loop = asyncio.get_event_loop()
    loop.set_debug(True)
    loop.run_until_complete(run_client())
 
except (OSError, asyncssh.Error) as e:
    logger.error("*** SSH connection failed ***")
    logger.error(e)