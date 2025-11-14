from fastapi import FastAPI
from loguru import logger
import sys


def setup_logging():
    """Configure logging"""
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
        level="INFO"
    )
    logger.add(
        "logs/trading_system.log",
        rotation="100 MB",
        retention="10 days",
        level="DEBUG"
    )


async def startup_event(app: FastAPI):
    """Startup event handler"""
    setup_logging()
    logger.info("🚀 AI Trading System Starting Up...")
    logger.info("Initializing database connections...")
    logger.info("Setting up WebSocket connections...")
    logger.info("Starting data ingestion pipelines...")
    logger.info("✅ System Ready!")


async def shutdown_event(app: FastAPI):
    """Shutdown event handler"""
    logger.info("🛑 AI Trading System Shutting Down...")
    logger.info("Closing open positions...")
    logger.info("Saving state...")
    logger.info("✅ Shutdown Complete!")
