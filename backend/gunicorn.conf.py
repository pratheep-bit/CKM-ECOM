"""
Gunicorn configuration for production deployment.
Uses Uvicorn workers for async FastAPI support.
"""

import multiprocessing

# Server socket
bind = "0.0.0.0:8000"

# Workers — 2 × CPU cores + 1 (classic formula)
workers = multiprocessing.cpu_count() * 2 + 1

# Use Uvicorn's worker class for async support
worker_class = "uvicorn.workers.UvicornWorker"

# Timeouts
timeout = 120          # Kill worker after 120s of inactivity
graceful_timeout = 30  # Give workers 30s to finish requests on shutdown
keepalive = 5          # Keep connections alive for 5s

# Logging
accesslog = "-"              # stdout
errorlog = "-"               # stdout
loglevel = "info"

# Security
limit_request_line = 8190
limit_request_fields = 100

# Restart workers periodically to prevent memory leaks
max_requests = 1000
max_requests_jitter = 50
