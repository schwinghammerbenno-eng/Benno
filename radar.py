#!/usr/bin/env python3
"""
US News Radar — entry point.

Usage:
    python radar.py             # starts on port 8001
    python radar.py --port 9000 # custom port
"""
import argparse
import uvicorn

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="US News Radar server")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8001)
    parser.add_argument("--reload", action="store_true", default=False)
    args = parser.parse_args()

    uvicorn.run(
        "radar.app:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level="info",
    )
