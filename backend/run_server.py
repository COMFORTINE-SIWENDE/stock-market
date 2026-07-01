#!/usr/bin/env python
"""
Simple script to run the aiohttp server
"""
from app.server import create_app
from aiohttp import web
from app.utils.logger import logger

if __name__ == "__main__":
    logger.info("Starting NSE Stock Market Server on http://0.0.0.0:8000")
    app = create_app()
    web.run_app(app, host="0.0.0.0", port=8000)
