"""Block until PostgreSQL accepts TCP connections.

Runs before uvicorn in the container so the API never boots against a
database that is still starting, regardless of depends_on support.
"""

import os
import socket
import sys
import time
from urllib.parse import urlsplit

url = os.environ.get("DATABASE_URL", "postgresql+psycopg://punto:punto@db:5432/punto")
parts = urlsplit(url)
host = parts.hostname or "db"
port = parts.port or 5432

deadline = time.monotonic() + 60
while True:
    try:
        with socket.create_connection((host, port), timeout=2):
            print(f"Database reachable at {host}:{port}", flush=True)
            sys.exit(0)
    except OSError as exc:
        if time.monotonic() > deadline:
            print(f"Database NOT reachable at {host}:{port}: {exc}", flush=True)
            sys.exit(1)
        time.sleep(1)
