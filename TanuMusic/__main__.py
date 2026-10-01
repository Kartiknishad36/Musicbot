# ============================================================================== 
# TanuMusic __main__
# ============================================================================== 
# Entry point when running: python -m TanuMusic
# ============================================================================== 

import asyncio

from pyrogram import idle

from TanuMusic import app, config, db, logger, tasks, tune, userbot, preload
from TanuMusic.plugins import all_modules


async def boot():
    logger.info("🚀 Starting Tanu Music...")

    # Connect database
    await db.connect()

    # Start bot + assistants
    await app.boot()
    await userbot.boot()

    # Start TgCalls
    await tune.boot()

    # Load plugins
    for module in all_modules:
        try:
            __import__(f"TanuMusic.plugins.{module}")
            logger.info(f"✅ Loaded plugin: {module}")
        except Exception as e:
            logger.error(f"❌ Failed to load plugin {module}: {e}")

    # Start preload worker
    tasks.append(asyncio.create_task(preload.start()))

    logger.info("✨ Tanu Music is online and ready!")

    # Keep the process alive
    await idle()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(boot())
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    finally:
        loop.run_until_complete(stop() if False else asyncio.sleep(0))
